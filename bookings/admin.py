from django.contrib import admin

from bookings.models  import *

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'room', 'check_in_date', 'check_out_date', 'status', 'created_at')
    list_filter = ('status', 'check_in_date', 'check_out_date')
    search_fields = ('customer__username', 'room__room_number')

@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ('customer', 'room', 'check_in_date', 'check_out_date', 'status', 'archived_at')
    search_fields = ('customer__username', 'room__room_number')
