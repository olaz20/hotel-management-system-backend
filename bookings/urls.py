from django.urls import path, include
from bookings.views import *
from . import views
from rest_framework_nested import routers


router = routers.SimpleRouter()
router.register("bookings", views.BookingViewSet, basename='bookings')

urlpatterns = [
    path('', include(router.urls)),  
    path('booking-history/', BookingHistoryView.as_view(), name='booking-history'),
]
