from django.contrib import admin
from .models import Room, RoomType, Review

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_capacity', 'description', 'slug')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'availability', 'price', 'description')
    search_fields = ('room_number', 'description')
    list_filter = ('availability', 'room_type')
    ordering = ('room_number',)
    list_editable = ('availability', 'price')  # Allows inline editing of these fields

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'rating', 'date_posted', 'review')
    search_fields = ('review', 'user__username', 'room__room_number')  # Search by review text, user, and room
    list_filter = ('rating', 'date_posted')  # Filter reviews by rating and date
    ordering = ('-date_posted',)  # Orders by newest reviews first
