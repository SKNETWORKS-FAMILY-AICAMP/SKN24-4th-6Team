"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
  path("admin/", admin.site.urls),
  path("api/users/", include("accounts.urls")),
  path("chat/", include("chat.urls")),
  path('contract/', include('contract.urls')),
  path("", include("health.urls")),
  # HTML pages
  path("login/", TemplateView.as_view(template_name="accounts/login.html"), name="page-login"),
  path("signup/", TemplateView.as_view(template_name="accounts/signup.html"), name="page-signup"),
  path("password-reset/", TemplateView.as_view(template_name="accounts/password_reset.html"), name="page-password-reset"),
  path("", TemplateView.as_view(template_name="index.html"), name="page-home"),
  path("threads/", TemplateView.as_view(template_name="chat/thread_list.html"), name="page-thread-list"),
  path("threads/<uuid:pk>/", TemplateView.as_view(template_name="chat/thread_detail.html"), name="page-thread-detail"),

  # API URLs
]
