from django.urls import path

from chat import views

app_name = "chat"

urlpatterns = [
  path("", views.ChatPageView.as_view(), name="chat-page"),
  path("<uuid:chatroom_id>/", views.ChatPageView.as_view(), name="chat-page-detail"),
]
