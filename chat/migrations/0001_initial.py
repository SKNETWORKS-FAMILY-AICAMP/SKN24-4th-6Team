import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Chatroom",
            fields=[
                (
                    "chatroom_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("last_chat_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("title", models.CharField(default="", max_length=100, null=True)),
                ("has_contract", models.BooleanField(default=False)),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chatrooms",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-last_chat_at"],
            },
        ),
        migrations.CreateModel(
            name="Chat",
            fields=[
                (
                    "chat_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("user", "user"),
                            ("assistant", "assistant"),
                            ("system", "system"),
                        ],
                        max_length=20,
                    ),
                ),
                ("content", models.TextField(null=True)),
                (
                    "chatroom_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chats",
                        to="chat.chatroom",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
