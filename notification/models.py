from django.db import models
from hotel_management import settings
# Create your models here.
class Notification(models.Model):
    class NotificationType(models.TextChoices):
        BOOKING_CONFIRMATION = 'booking_confirmation', 'Booking Confirmation'
        PAYMENT_SUCCESS = 'payment_success', 'Payment Success'
        REMINDER = 'reminder', 'Reminder'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.recipient} ({self.notification_type})"

    class Meta:
        ordering = ['-created_at']
