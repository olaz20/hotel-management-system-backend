from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from .models import Booking, BookingHistory
from rest_framework.permissions import IsAuthenticated, AllowAny,  BasePermission
from .serializers import BookingSerializer, BookingHistorySerializer
from rest_framework.permissions import IsAuthenticated
from rooms.models import Room
from rest_framework import generics

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow safe methods (e.g., GET) for any user
        if request.method in ['GET']:
            return True
        # Allow only the creator of the review to modify or delete it
        return obj.customer == request.user


class BookingViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsOwner]  # Ensure only authenticated users can access

    def get_queryset(self):
        """
        Return bookings related to the logged-in user.
        """
        user = self.request.user
        return Booking.objects.filter(customer=user)

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to release room if booking is canceled.
        """
        instance = self.get_object()
        instance.room.availability = Room.AvailabilityStatus.AVAILABLE
        instance.room.save()
        self.perform_destroy(instance)
        return Response({"message": "Booking canceled and room marked as available."}, status=status.HTTP_204_NO_CONTENT)
    
class BookingHistoryView(generics.ListAPIView):
    """
    Retrieve booking history for the logged-in user.
    """
    serializer_class = BookingHistorySerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Filter booking history by the logged-in user.
        """
        user = self.request.user
        return BookingHistory.objects.filter(customer=user)