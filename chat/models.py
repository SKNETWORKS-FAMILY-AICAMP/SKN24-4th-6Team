from django.conf import settings
from django.db import models

from core.models import TimestampedModel


class Thread(TimestampedModel):
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="threads",
  )
  title = models.CharField(max_length=200, blank=True, default="")

  class Meta:
    ordering = ["-updated_at"]

  def __str__(self) -> str:
    return self.title or f"Thread {self.pk}"


class Message(TimestampedModel):
  class Role(models.TextChoices):
    USER = "user", "user"
    ASSISTANT = "assistant", "assistant"
    SYSTEM = "system", "system"

  thread = models.ForeignKey(
    Thread,
    on_delete=models.CASCADE,
    related_name="messages",
  )
  role = models.CharField(max_length=16, choices=Role.choices)
  content = models.TextField()

  class Meta:
    ordering = ["created_at"]
