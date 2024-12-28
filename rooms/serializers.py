from rest_framework import serializers
from rooms.models import *


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ['id','name', 'description','slug','max_capacity','facilities']
        
class RoomSerializer(serializers.ModelSerializer):
    room_type = serializers.PrimaryKeyRelatedField(
        queryset=RoomType.objects.all()
    )
    avg_rating = serializers.SerializerMethodField()
    class Meta:
        model = Room
        fields = ['id', 'room_type', 'room_number','availability', 'price', 'description', 'image', 'avg_rating']
    def get_avg_rating(self, obj):
        # Access the dynamically annotated avg_rating or return None
        return getattr(obj, 'avg_rating', None)
    def validate_room_number(self, value):
        if not value:
            raise serializers.ValidationError("Room number is required.")
        return value
    def create(self, validated_data):
        room_type = validated_data.pop('room_type', None)
        
        room_number = validated_data.get('room_number')
        room_number = validated_data.pop('room_number')
        if not room_number:
            raise serializers.ValidationError({"room_number": "This field is required."})
        if Room.objects.filter(room_number=room_number).exists():
            raise serializers.ValidationError({"room_number": "This room number already exists."})
        room = Room.objects.create(room_type=room_type, room_number=room_number ,**validated_data)
        return room
    
class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'username', 'rating', 'review']
    def create(self, validated_data):
    
        return Review.objects.create(**validated_data)