from rest_framework import serializers
from .models import *
from rooms.serializers import RoomSerializer
from django.utils.timezone import now
from django.core.mail import send_mail


class BookingSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.filter(availability='available'))
    customer = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Booking
        fields = ['id', 'room', 'customer', 'check_in_date', 'check_out_date','capacity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status','created_at', 'updated_at']
        
    def validate(self, data):
        """Ensure check-in date is before check-out date."""
        room=data.get('room')
        check_in_date = data.get('check_in_date')
        check_out_date = data.get('check_out_date')
        capacity = data.get('capacity')
        
        if room.availability != Room.AvailabilityStatus.AVAILABLE:
            raise serializers.ValidationError({'room': f'Room {room.room_number} is not available'})
        
    
        if check_in_date >= check_out_date:
            raise serializers.ValidationError("Check-out date must be after check-in date.")

        # Prevent bookings in the past
        if check_in_date < now().date():
            raise serializers.ValidationError("Check-in date cannot be in the past.")
        
        request = self.context.get('request')
        current_booking_id = None
        if request and request.method in ['PUT', 'PATCH']:
           current_booking_id = self.instance.id if self.instance else None
           
        overlapping_bookings = Booking.objects.filter(
            room=room, check_in_date__lte=check_out_date, check_out_date__gte = check_in_date,
        ).exclude(id=current_booking_id)
        
        if overlapping_bookings.exists():
            raise serializers.ValidationError(
                f"The room {room.room_number} is already booked from {overlapping_bookings.first().check_in_date} to {overlapping_bookings.first().check_out_date}.")
        room_type = room.room_type
        if room_type.max_capacity < capacity:
            raise serializers.ValidationError(f"The room {room.room_number} cannot accommodate more than {room_type.max_capacity} guests.")
        return data
    def create(self, validated_data):
        """Automatically associate the booking with the logged-in user."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({"customer": "A logged-in user is required to make a booking."})
        # Attach the logged-in user as the customer
        validated_data['status'] = Booking.BookingStatus.COMPLETED
        validated_data['customer'] = request.user
        booking = super().create(validated_data)
        user_email = request.user.email
        send_mail(
            subject="Booking Confirmation",
            message=f"Dear {request.user.username},\n\n"
                    f"Your booking for room {booking.room.room_number} has been confirmed.\n"
                    f"Check-in Date: {booking.check_in_date}\n"
                    f"Check-out Date: {booking.check_out_date}\n"
                    f"Guests: {booking.capacity}\n\n"
                    "Thank you for booking with us!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return booking
    
class BookingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingHistory
        fields = [
            'id', 'booking', 'customer', 'room', 'check_in_date', 
            'check_out_date', 'status', 'created_at', 'updated_at', 'archived_at'
        ]
        read_only_fields = ['id', 'archived_at']
