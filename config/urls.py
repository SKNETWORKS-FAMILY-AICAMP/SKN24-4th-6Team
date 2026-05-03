"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
  path("admin/", admin.site.urls),
  path("api/users/", include("accounts.urls")),
  path("mypage/", include("mypage.urls")),
  path("chat/", include("chat.urls")),
  path("contract/", include("contract.urls")),
  path("", include("health.urls")),
  # HTML pages
  path("login/", TemplateView.as_view(template_name="index.html"), name="page-login"),
  path("signup/", TemplateView.as_view(template_name="index.html"), name="page-signup"),
  path(
    "password-reset/",
    TemplateView.as_view(template_name="index.html"),
    name="page-password-reset",
  ),
  path("", TemplateView.as_view(template_name="index.html"), name="page-home"),
  # API URLs
  path("api/v1/", include("chat.api_urls")),
  path("api/v1/", include("mypage.api_urls")),
]
