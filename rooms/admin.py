from django.contrib import admin
from rooms.models import *
# Register your models here.
@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'availability', 'price', 'description')  # Add 'availability' to list_display
    list_filter = ('availability',) 
    search_fields = ('room_number', 'description')