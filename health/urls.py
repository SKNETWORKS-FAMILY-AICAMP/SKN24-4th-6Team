from django.urls import path

from health import views

app_name = "health"

urlpatterns = [
  path("healthz", views.healthz, name="healthz"),
]
