from django.db import models
from django.conf import settings
from rooms.models import Room
# Create your models here.
class Booking(models.Model):
    class BookingStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending',
        CONFIRMED = 'CONFIRMED', 'Confirmed',
        CANCELED = 'CANCELED', 'Canceled',
        COMPLETED = 'completed', 'Completed'
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    capacity=models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Booking by {self.customer} for Room {self.room.room_number} ({self.status})"
    class Meta:
        ordering = ['-created_at']

    
class BookingHistory(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="history")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_history")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="booking_history")
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    archived_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"History for Booking {self.booking.id} ({self.status})"
    
    class Meta:
        ordering = ['-archived_at']