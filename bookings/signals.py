from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Booking, BookingHistory

@receiver(post_save, sender=Booking)
def create_or_update_booking_history(sender, instance, created, **kwargs):
    """
    Create or update the booking history whenever a booking is saved.
    """
    BookingHistory.objects.update_or_create(
        booking=instance,
        defaults={
            'customer': instance.customer,
            'room': instance.room,
            'check_in_date': instance.check_in_date,
            'check_out_date': instance.check_out_date,
            'status': instance.status,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }
    )

@receiver(post_delete, sender=Booking)
def delete_booking_history(sender, instance, **kwargs):
    """
    Delete the associated booking history when a booking is deleted.
    """
    BookingHistory.objects.filter(booking=instance).delete()
