from django.urls import path

from chat import views

app_name = "chat-api"

urlpatterns = [
  path(
    "chatrooms",
    views.ChatroomListCreateView.as_view(),
    name="chatroom-list",
  ),
  path(
    "chatrooms/<uuid:pk>",
    views.ChatroomDetailView.as_view(),
    name="chatroom-detail",
  ),
  path(
    "chatrooms/<uuid:pk>/messages",
    views.SendMessageView.as_view(),
    name="chatroom-send-message",
  ),
]
