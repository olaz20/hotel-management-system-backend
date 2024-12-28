from django.db import models
import uuid
import django_filters
from django.utils.text import slugify
from  django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
# Create your models here.
class RoomType(models.Model):
    id = models.BigIntegerField(primary_key=True, auto_created=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(null=True, blank=True)
    max_capacity = models.PositiveIntegerField(default=1)  # Number of people the room can accommodate
    facilities = models.JSONField(blank=True, null=True)# A list or description of available facilities
    
    def save(self, *args, **kwargs):
        if not self.slug:  # Only create a slug if it hasn't been set
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name

class Room(models.Model):
    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        OCCUPIED = 'occupied', 'Occupied'
        MAINTENANCE = 'maintenance', 'Under Maintenance'
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, unique=True)
    image = models.ImageField(upload_to='img', blank= True, null=True, default='')
    room_number = models.CharField(max_length=10, unique=True, null=False)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE , related_name="rooms")
    availability = models.CharField(
        max_length=20, 
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.AVAILABLE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True) 
    
    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name})"

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="reviews")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, default="")
    room = models.ForeignKey(Room , on_delete=models.CASCADE, related_name="reviews")
    date_posted = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review by {self.user.username} - {self.review[:30]}..."











class RoomFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='Minimum Price')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='Maximum Price')
    room_type = django_filters.CharFilter(field_name='room_type__name', lookup_expr='icontains', label='Room Type')
    availability = django_filters.ChoiceFilter(
        field_name='availability',
        choices=Room.AvailabilityStatus.choices,
        label='Availability Status'
    )

    class Meta:
        model = Room
        fields = ['min_price', 'max_price', 'room_type', 'availability']




class RoomTypeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Room Type Name')
    description = django_filters.CharFilter(lookup_expr='icontains', label='Description')
    max_capacity = django_filters.NumberFilter(field_name='max_capacity', lookup_expr='exact', label='Max Capacity')
    facilities = django_filters.CharFilter(lookup_expr='icontains', field_name='facilities', label='Facilities')
    class Meta:
        model = RoomType
        fields = ['name', 'description', 'max_capacity', 'facilities']  # List the fields you want to be filterable