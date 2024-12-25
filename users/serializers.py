from rest_framework import serializers
from .models import *
from rest_framework.validators import UniqueValidator
from django.contrib.auth.hashers import make_password

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
        print("is_staff_member:", attrs.get('is_staff_member'))
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
        
        # Check if email or username exists in PendingUser or User
        #if PendingUser.objects.filter(email=attrs['email']).exists() or User.objects.filter(email=attrs['email']).exists():
           # raise serializers.ValidationError({"email": "This email is already in use."})
        #if PendingUser.objects.filter(username=attrs['username']).exists() or User.objects.filter(username=attrs['username']).exists():
           # raise serializers.ValidationError({"username": "This username is already taken."})
        
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        confirm_password = validated_data.pop('confirm_password', None)
        
         # Remove existing PendingUser with the same email
        PendingUser.objects.filter(email=validated_data['email']).delete()
        # Store the data in the PendingUser model
        validated_data['password'] = make_password(password) 
        pending_user = PendingUser.objects.create(**validated_data)
        pending_user.save()
        
        # Optionally send a verification email here
        # send_verification_email(pending_user)
        
        return pending_user

   
class AuthCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    class Meta:
        model = User
        fields = ["code"]
    