from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import *
# Register your models here.


@admin.register(PreRegisteredStaff)
class PreRegisteredStaffAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'work_id', 'created_at')
    search_fields = ('username', 'email', 'work_id')
    list_filter = ('created_at',)
    
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ( 'phone_number', 'address', 'work_id' )}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('phone_number', 'address', 'work_id')}),
    )

@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'password', 'is_staff_member', 'work_id')
    search_fields =('username', 'email','work_id')
    list_filter = ('is_staff_member', 'work_id')
