from rest_framework import serializers
from .models import *
from rest_framework.validators import UniqueValidator
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.hashers import check_password

class UserSignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    confirm_password = serializers.CharField(write_only=True, required=True)
    is_staff_member = serializers.BooleanField(default=False)  # Default is False
    work_id = serializers.CharField(required=False)

    class Meta:
        model = PendingUser  # Store in PendingUser instead of User
        fields = ('username', 'email', 'password', 'confirm_password', 'is_staff_member', 'work_id')
    
    def validate(self, attrs):
        attrs['is_staff_member'] = bool(attrs.get('is_staff_member'))
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if attrs.get('is_staff_member') and not attrs.get('work_id'):
            raise serializers.ValidationError("Staff must provide a valid Work ID.")
        
        # Check if work_id and email exist in the pre-added records by admin
        if attrs.get('is_staff_member'):
            email = attrs.get('email')
            work_id = attrs.get('work_id')

            if not email or not work_id:
                raise serializers.ValidationError({
                    "email/work_id": "Both email and Work ID are required for staff members."
                })
            try:
                PreRegisteredStaff.objects.get(email=email, work_id=work_id)
            except PreRegisteredStaff.DoesNotExist:
                raise serializers.ValidationError(
                    {"email/work_id": "The provided email and Work ID are not in our records."}
                )
        
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        confirm_password = validated_data.pop('confirm_password', None)
         # Remove existing PendingUser with the same email
        is_staff_member = validated_data.get('is_staff_member', False)
        work_id = validated_data.get('work_id', None) 
        PendingUser.objects.filter(email=validated_data['email']).delete()
        # Store the data in the PendingUser model
        pending_user = PendingUser.objects.create(**validated_data)
        pending_user.save()
        
        return pending_user

   
class AuthCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    class Meta:
        model = User
        fields = ["code"]
        
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)
    work_id = serializers.CharField(required=False)
    is_staff_member = serializers.BooleanField(default=False)
    
    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        work_id = data.get("work_id")
        is_staff_member = data.get("is_staff_member")

        # Ensure that either email or work_id is provided
        if not email and not work_id:
            raise serializers.ValidationError("Either email or work ID must be provided.")

        # If work_id is provided, check if the user exists
        if work_id:
            try:
                user = User.objects.get(work_id=work_id)
                if user.is_staff_member != is_staff_member:  # Check if the staff member status matches
                    raise serializers.ValidationError("Work ID does not belong to the specified user type.")
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid work ID or password.")
        
        # If email is provided, check if the user exists
        elif email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password.")

        else:
            raise serializers.ValidationError("Invalid credentials.")

        # Check if the password matches
        if not check_password(password, user.password):
            raise serializers.ValidationError("Invalid email, work ID, or password.")

        # Check if the user account is active
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        # Check if the user is verified
        if not getattr(user, "is_verified", False):  # If is_verified is not set, treat as False
            raise serializers.ValidationError("User account is not verified.")

        # Return the user object to be used later (for example, in the view or token generation)
        return user
    
class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    redirect_url = serializers.CharField(max_length=500, required=False, read_only=True)

    class Meta:
        fields = ['email']
        
class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)
    
    class Meta:
        fields = ['password', 'token', 'uidb64',]

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)

            user.set_password(password)
            user.save()

            return (user)
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)
        return super().validate(attrs)
        
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    auth_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
    class Meta:
        model = User
        fields = ['email', 'auth_code', 'new_password']

class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        user = self.context['request'].user
        password = attrs.get('password')

        if password:
            # Verify the user's password
            if not user.check_password(password):
                raise serializers.ValidationError({'password': 'Incorrect password.'})
        
        return attrs
    
