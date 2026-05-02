from django.urls import path

from chat import views

app_name = "chat"

urlpatterns = [
  path("", views.ChatPageView.as_view(), name="chat-page"),  # 추가
  path("chatrooms", views.ChatroomListCreateView.as_view(), name="chatroom-list"),
  path("chatrooms/<uuid:pk>", views.ChatroomDetailView.as_view(), name="chatroom-detail"),
  path(
    "chatrooms/<uuid:pk>/chats",
    views.SendMessageView.as_view(),
    name="chatroom-send-message",
  ),
]