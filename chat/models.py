from django.conf import settings
from django.db import models
# from core.models import User
import uuid

class Chatroom(models.Model):        # AUTH_USER_MODEL = "core.User"
  user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chatrooms")
  # user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chatrooms")
  chatroom_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  last_chat_at = models.DateTimeField(auto_now=True)
  created_at = models.DateTimeField(auto_now_add=True)
  title = models.CharField(max_length=100, null=True, default="")
  has_contract = models.BooleanField(default=False)

  class Meta:
    ordering = ["-last_chat_at"]

  def __str__(self) -> str:     # Django 관리자 페이지(admin)나 shell에서 객체를 출력할 때 보여주는 텍스트를 정의
    return self.title or f"Chatroom {self.pk}"



class Chat(models.Model):
  class Role(models.TextChoices):
    USER = "user", "user"
    ASSISTANT = "assistant", "assistant"
    SYSTEM = "system", "system"

  chatroom_id = models.ForeignKey(Chatroom, on_delete=models.CASCADE, related_name="chats")
  chat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  created_at = models.DateTimeField(auto_now_add=True)
  role = models.CharField(max_length=20, choices=Role.choices)
  content = models.TextField(null=True)

  class Meta:
    ordering = ["created_at"]
