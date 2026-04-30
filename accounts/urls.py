from django.urls import path
from rest_framework_simplejwt.views import (
  TokenBlacklistView,
  TokenObtainPairView,
  TokenRefreshView,
)

from accounts import views

app_name = "accounts"

urlpatterns = [
  path("register", views.RegisterView.as_view(), name="register"),
  path("token", TokenObtainPairView.as_view(), name="token-obtain"),
  path("token/refresh", TokenRefreshView.as_view(), name="token-refresh"),
  path("token/blacklist", TokenBlacklistView.as_view(), name="token-blacklist"),
]
