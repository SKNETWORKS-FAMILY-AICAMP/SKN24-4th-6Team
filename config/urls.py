"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
  path("admin/", admin.site.urls),
  path("api/auth/", include("accounts.urls")),
  path("chat/", include("chat.urls")),
  path("", include("health.urls")),
]
