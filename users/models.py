from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from django.contrib.auth.hashers import make_password
from cryptography.fernet import Fernet
from django.conf import settings

# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    work_id = models.CharField(max_length = 20, unique = True, null = True, blank=True, help_text="Unique Work ID for staff members")
    is_staff_member = models.BooleanField(default=False)  # True for staff, False for customers
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
            
    def __str__(self):
        return self.username
    
if not hasattr(settings, "ENCRYPTION_KEY"):
    settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

cipher = Fernet(settings.ENCRYPTION_KEY)

class PendingUser(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_staff_member = models.BooleanField(default=False)
    work_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verification_code = models.CharField(max_length=6)
    # Add more fields as needed
    
    def save(self, *args, **kwargs):
        # Encrypt the password before saving
        if not self.password.startswith("gAAAAAB"):  # Check if already encrypted
            self.password = cipher.encrypt(self.password.encode()).decode()
        
        if self.is_staff_member and not self.work_id:
            raise ValueError("Staff must have a valid Work ID.")
        super().save(*args, **kwargs)
    def decrypt_password(self):
        # Decrypt the password when needed
        return cipher.decrypt(self.password.encode()).decode()
class AuthCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)  # 6-digit code
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_code(self):
        self.code = str(random.randint(100000, 999999))  # Generate a 6-digit code
        self.save()
        
class PreRegisteredStaff(models.Model):
    email = models.EmailField(unique=True)
    work_id = models.CharField(max_length=100 , unique=True, null=True,blank=False, help_text="Unique Work ID for staff members")
    created_at = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=150, unique=True)
    def __str__(self):
        return self.email
     
