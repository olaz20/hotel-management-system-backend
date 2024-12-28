from rooms.serializers import *
from rooms.models import *
from rest_framework import permissions
from users.models import *
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny,  BasePermission
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.db.models import Avg
from rest_framework.exceptions import ValidationError


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_staff_member:
            return True
        return False
    
class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff_member:
            return True
        return False
class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow safe methods (e.g., GET) for any user
        if request.method in ['GET']:
            return True
        # Allow only the creator of the review to modify or delete it
        return obj.user == request.user
    
class RoomTypeViewSet(ModelViewSet):
    queryset = RoomType.objects.all()
    serializer_class = RoomTypeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RoomTypeFilter
    search_fields = ['name','description']
    pagination_class = PageNumberPagination
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update','destroy']:
           self.permission_classes = [IsAuthenticated,IsStaff]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
           
class RoomViewSet(ModelViewSet):
    queryset = Room.objects.all().annotate(avg_rating=Avg('reviews__rating'))
    serializer_class = RoomSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RoomFilter
    pagination_class = PageNumberPagination
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'avg_rating']
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update','destroy']:
           self.permission_classes = [IsAuthenticated,IsStaff]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    
class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = PageNumberPagination
    search_fields = ['review', 'room__room_number', 'user__username']
    ordering_fields = ['created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsOwner]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    def get_queryset(self):
        return Review.objects.filter(room_id=self.kwargs['room_pk_pk'])
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  # Add the request object to context
        context["room_id"] = self.kwargs["room_pk_pk"]
        return context
    def perform_create(self, serializer):
        room_id = self.kwargs['room_pk_pk']
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return ValidationError({"error": "Room not found"})
        serializer.save(room=room, user=self.request.user)