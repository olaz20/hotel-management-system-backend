from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
from .models import *
from users.serializers import *
from django.urls import reverse
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import Signer
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import make_password
import random

from hotel_management.utils import *

class SignUpView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserSignUpSerializer
    def post(self, request):
        serializer = UserSignUpSerializer(data=request.data)
        if serializer.is_valid():
            # Save the user data
            user_data = serializer.validated_data
            if user_data.get('is_staff_member') and not user_data.get('work_id'):
                return Response({"error": "Staff must provide a valid Work ID."}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            
            # Generate a random authentication code
            auth_code = random.randint(100000, 999999)
            
            # Store auth code and user data in cache
            email = user_data["email"]
            username = user_data["username"]
            password = user_data["password"]
            pending_user, created = PendingUser.objects.update_or_create(
                email=email,
                defaults={
                    "username": username,
                    "password": password,
                    "is_staff_member": user_data.get("is_staff_member", False),
                    "work_id": user_data.get("work_id"),
                    "verification_code": auth_code,
                },
            )
            cache.set(f"auth_code_{email}", auth_code, timeout=600)  # Cache for 10 minutes
            cache.set(f"user_data_{email}", user_data, timeout=600)  # Cache for 10 minutes
            
            # Generate a signed token for the user
            signer = Signer()
            signed_data = signer.sign(email)
            
            # Generate the email verification link
            username = user_data["username"]
            current_site = get_current_site(request).domain
            relative_link = reverse('email-verify')  # URL pattern name for email verification
            absurl = f'http://{current_site}{relative_link}?token={signed_data}'
            
            # Construct the email body
            email_body = (
                f"Hi {username},\n\n"
                f"Use the link below to verify your email:\n{absurl}\n\n"
                f"Authentication Code: {auth_code}\n"
                "Enter this code on the registration page to complete your registration.\n"
            )
            
            data = {
                "email_body": email_body,
                "to_email": email,
                "email_subject": "Verify your email and authentication code",
            }
            try:
                Util.send_email(data)
            except Exception as e:
                return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            return Response({
                "message": "Registration initiated. Please check your email to verify your account."
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ResendCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the email exists in the PendingUser table
        try:
            pending_user = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({"error": "No registration pending for this email."}, status=status.HTTP_404_NOT_FOUND)

        # Generate and cache a new auth code
        auth_code = random.randint(100000, 999999)
        cache.set(f"auth_code_{email}", auth_code, timeout=600)

        # Send email with the new verification link and code
        signer = Signer()
        signed_data = signer.sign(email)
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        absurl = f'https://{current_site}{relative_link}?token={signed_data}'

        email_body = (
            f"Hi {pending_user.username},\n\n"
            f"Use the link below to verify your email:\n{absurl}\n\n"
            f"Authentication Code: {auth_code}\n"
            "Enter this code on the registration page to complete your registration.\n"
        )
        data = {
            "email_body": email_body,
            "to_email": email,
            "email_subject": "Verify your email and authentication code",
        }
        try:
            Util.send_email(data)
        except Exception as e:
            return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "A new verification code has been sent to your email."
        }, status=status.HTTP_200_OK)

class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        code = request.data.get('code')

        if not email or not code:
            return Response({"error": "Email and code are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the verification code from the cache
        cached_code = cache.get(f"auth_code_{email}")
        if not cached_code:
            return Response({"error": "Verification code expired or not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the provided code matches the cached code
        if str(cached_code) != str(code):
            return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if the email exists in PendingUser
            pending_user = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({"error": "No registration pending for this email."}, status=status.HTTP_404_NOT_FOUND)

        # Create the actual user account from PendingUser details
        user = User.objects.create_user(
            username=pending_user.username,
            email=pending_user.email,
            password=pending_user.password,
            is_staff_member=pending_user.is_staff_member,
            work_id=pending_user.is_staff_member
        )
        user.is_active = True
        user.is_verified=True  # Activate the account
        user.save()

        # Clean up: Delete the PendingUser entry and clear the cached code
        pending_user.delete()
        cache.delete(f"auth_code_{email}")

        return Response({"message": "Email successfully verified and account created. You can now log in."}, status=status.HTTP_200_OK)

class EmailVerifyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Invalid request, no token provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        signer = Signer()
        try:
            # Unsigned token to get the email
            email = signer.unsign(token)

            # Get auth code from cache (token expiration handled implicitly by cache timeout)
            auth_code = cache.get(f"auth_code_{email}", None)
            if not auth_code:
                return Response({"error": "Token expired or invalid."}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the pending user based on email
            try:
                pending_user = PendingUser.objects.get(email=email)
            except PendingUser.DoesNotExist:
                return Response({"error": "Pending user not found."}, status=status.HTTP_400_BAD_REQUEST)

            # Create the actual user in the User table
            user = User.objects.create_user(
                username=pending_user.username,
                email=pending_user.email,
                password=pending_user.password,  # Password is hashed automatically with create_user
            )

            # Update user status after verification
            user.is_verified = True
            user.is_active = True
            user.save()

            # Delete the pending user as they are now verified
            pending_user.delete()

            return Response({"message": "Email verified successfully!"}, status=status.HTTP_200_OK)

        except BadSignature:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        work_id = request.data.get('work_id', None)  # Optional for non-staff users

        # Authenticate the user by email
        user = authenticate(request, username=email, password=password)

        if user:
            # Check if the user is a staff member
            if user.is_staff:
                if not work_id:
                    return JsonResponse(
                        {"error": "Staff members must provide a valid work ID."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Add logic to validate the work ID if required
                if user.work_id != work_id:  # Assuming a `work_id` field exists in the user model
                    return JsonResponse(
                        {"error": "Invalid work ID."},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

            if not user.is_verified:
                return JsonResponse(
                    {"error": "Your email is not verified. Please verify your email to log in."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Log in the user
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,)
        else:
            return JsonResponse(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

User = get_user_model()

class VerifiedUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and user.is_verified:  # Custom logic
                return user
        except User.DoesNotExist:
            return None
