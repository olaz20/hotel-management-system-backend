from django.db import models
from django.contrib.auth.models import AbstractUser
import random
# Create your models here.

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
    ]
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    work_id = models.CharField(max_length = 20, unique = True, null = True, blank=True, help_text="Unique Work ID for staff members")
    is_staff_member = models.BooleanField(default=False)  # True for staff, False for customers
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if self.user_type == 'customer':
            self.work_id = None
            super().save(*args, **kwargs)
            
    def __str__(self):
        return self.username
    
class PendingUser(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_staff_member = models.BooleanField(default=False)
    work_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verification_code = models.CharField(max_length=6)
    # Add more fields as needed

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
     

class StaffProfile(models.Model):
    # Link to the Django User model (assuming every staff member is also a User)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=200)
    # Staff-specific fields
    work_id = models.CharField(max_length=100, unique=True, null=True,help_text="Unique Work ID for staff members")
    department = models.CharField(max_length=255, null=True, blank=True)  # The department of the staff
    position = models.CharField(max_length=255, null=True, blank=True)  # The position or job title
    date_joined = models.DateTimeField(auto_now_add=True)  # When the staff member joined the organization
    is_active = models.BooleanField(default=True)  # To mark whether the staff is currently active or not
    profile_picture = models.ImageField(upload_to='staff_pics/', null=True, blank=True)  # Optional field for a staff profile picture
    is_registered = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username} - {self.position}"

    class Meta:
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'
        
