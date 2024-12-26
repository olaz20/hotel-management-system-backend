from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import *
from users.serializers import *
from django.urls import reverse
import os
from django.contrib.auth.models import Group
from django.http import HttpResponsePermanentRedirect
from django.utils.encoding import smart_bytes, smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.cache import cache
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import Signer
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
import random
from django.utils.crypto import get_random_string
from hotel_management.utils import *


User = get_user_model()


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
        plain_password = pending_user.decrypt_password()
        # Create the actual user account from PendingUser details
        user = User.objects.create_user(
            username=pending_user.username,
            email=pending_user.email,
            password=plain_password,
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
                print(f"Found PendingUser: {pending_user.username}, is_staff_member: {pending_user.is_staff_member}, work_id: {pending_user.work_id}")
            except PendingUser.DoesNotExist:
                return Response({"error": "Pending user not found."}, status=status.HTTP_400_BAD_REQUEST)
            # Create the actual user in the User table
            plain_password = pending_user.decrypt_password()
            user = User.objects.create_user(
                username=pending_user.username,
                email=pending_user.email,
                password=plain_password,  # Password is hashed automatically with create_user
                is_staff_member=pending_user.is_staff_member,
                work_id=pending_user.work_id if pending_user.is_staff_member else None  # Set work_id only for staff members
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


class VerifiedUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and user.is_verified:  # Custom logic
                return user
        except User.DoesNotExist:
            return None


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializers = LoginSerializer
    def post(self, request):
        serializers = LoginSerializer(data=request.data)
        if serializers.is_valid():
            user = serializers.validated_data
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access":str(refresh.access_token),
            })
        return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get the refresh token from the request data
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "Refresh token is required."}, status=400)
            
            # Blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Logout successful."}, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
        
class RequestPasswordEmail(generics.GenericAPIView): 
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        # Validate the request data using serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']  # Safely get email after validation

        # Check if a user with this email exists
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            
            # Generate a unique token for the user
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            # Generate an OTP and store it in the cache
            reset_code = get_random_string(length=6, allowed_chars='0123456789')
            cache.set(f"password_reset_code_{email}", reset_code, timeout=900)  # Valid for 15 minutes

            # Construct the reset URL
            current_site = get_current_site(request=request).domain
            relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            redirect_url = request.data.get('redirect_url', '')
            absurl = f"http://{current_site}{relative_link}?redirect_url={redirect_url}"

            # Email body with link and code
            email_body = (
                f"Hello,\n\n"
                f"Use the link below to reset your password:\n{absurl}\n\n"
                f"Alternatively, use this code to reset your password: {reset_code}\n\n"
                f"If you didn't request a password reset, please ignore this email."
            )

            # Send the email
            data = {
                'email_body': email_body,
                'to_email': user.email,
                'email_subject': 'Reset Your Password'
            }
            Util.send_email(data)

            # Respond with success
            return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)

        # User with provided email does not exist
        return Response({'error': 'No user found with this email address'}, status=status.HTTP_404_NOT_FOUND)
    
class CustomRedirect(HttpResponsePermanentRedirect):
    permission_classes = [AllowAny]
    allowed_schemes = [os.environ.get('APP_SCHEME'), 'http', 'https']

class PasswordTokenCheckAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        # Use localhost as the default redirect URL during development
        redirect_url = request.GET.get('redirect_url', 'http://localhost:3000')

        try:
            # Decode the user ID
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            # Validate the token
            if not PasswordResetTokenGenerator().check_token(user, token):
                return CustomRedirect(f"{redirect_url}?token_valid=False&message=Invalid or expired token")

            # If token is valid, redirect with success parameters
            return CustomRedirect(
                f"{redirect_url}?token_valid=True&message=Credentials Valid&uidb64={uidb64}&token={token}"
            )

        except DjangoUnicodeDecodeError:
            # Handle decoding errors gracefully
            return Response({'error': 'Invalid UID encoding'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            # Handle case where user does not exist
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # Log unexpected errors for easier debugging in development
            print(f"Unexpected error in PasswordTokenCheckAPI: {str(e)}")
            return Response({'error': 'Unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SetNewPasswordAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)
class ValidateOTPAndResetPassword(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        # Extract request data
        email = request.data.get('email', '').strip()
        auth_code = request.data.get('auth_code', '')
        new_password = request.data.get('new_password', '').strip()
        try:
            auth_code = int(auth_code)
        except ValueError:
            return Response({'error': 'Invalid authentication code format. Must be a numeric value.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not email or not auth_code or not new_password:
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
        stored_auth_code = int(cache.get(f"password_reset_code_{email}"))  
        if stored_auth_code is None:
            return Response({"error": "Authentication code expired or not found."}, status=status.HTTP_400_BAD_REQUEST)


        if not stored_auth_code:
            return Response({"error": "Authentication code expired or not found."}, status=status.HTTP_400_BAD_REQUEST)

        if stored_auth_code != auth_code:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.filter(email=email).exists():
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        # Clear the OTP
        cache.delete(f"password_reset_code_{email}")

        return Response({"success": "Password has been reset successfully."}, status=status.HTTP_200_OK)
    
class DeleteAccountView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteAccountSerializer

    def delete(self, request):
        # Validate the request
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Delete the user account
        user = request.user
        user.delete()

        return Response({'success': 'Your account has been deleted.'}, status=status.HTTP_204_NO_CONTENT)