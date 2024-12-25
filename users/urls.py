from django.urls import path, include
from . import views
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_nested import routers

router = routers.SimpleRouter()

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('email-verify/', views.EmailVerifyView.as_view(), name='email-verify'),
    path('resend-auth-code/', ResendCodeView.as_view(), name='resend_auth_code'),
    path('email-code-verify/', views.VerifyCodeView.as_view(), name='email-code-verify')
]

