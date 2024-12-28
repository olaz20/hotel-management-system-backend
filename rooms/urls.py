from django.urls import path, include
from . import views
from rooms.views import *

from rest_framework_nested import routers

router = routers.SimpleRouter()
router.register("categories", views.RoomTypeViewSet, basename="room-type")
router.register("rooms", views.RoomViewSet, basename="rooms")

rooms_router = routers.NestedSimpleRouter(router, "rooms", lookup="room_pk")
rooms_router.register("reviews", views.ReviewViewSet, basename="room-reviews")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(rooms_router.urls)),
]
