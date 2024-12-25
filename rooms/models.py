from django.db import models

# Create your models here.
class RoomType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Room(models.Model):
    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        OCCUPIED = 'occupied', 'Occupied'
        MAINTENANCE = 'maintenance', 'Under Maintenance'
        
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    availability = models.CharField(
        max_length=20, 
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.AVAILABLE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name})"
