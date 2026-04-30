from django.urls import path

from chat import views

app_name = "chat"

urlpatterns = [
  path("threads", views.ThreadListCreateView.as_view(), name="thread-list"),
  path("threads/<int:pk>", views.ThreadDetailView.as_view(), name="thread-detail"),
  path(
    "threads/<int:pk>/messages",
    views.SendMessageView.as_view(),
    name="thread-send-message",
  ),
]
