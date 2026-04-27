from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from chat.models import Thread


@pytest.fixture
def auth_client() -> tuple[APIClient, "object"]:
  user = get_user_model().objects.create_user(username="dana", password="x")
  client = APIClient()
  client.force_authenticate(user=user)
  return client, user


@pytest.mark.django_db
def test_unauthenticated_thread_list_is_401() -> None:
  client = APIClient()
  response = client.get("/chat/threads")
  assert response.status_code == 401


@pytest.mark.django_db
def test_create_thread_assigns_current_user(auth_client) -> None:
  client, user = auth_client
  response = client.post("/chat/threads", {"title": "t1"}, format="json")
  assert response.status_code == 201
  assert Thread.objects.get(pk=response.data["id"]).user == user


@pytest.mark.django_db
def test_thread_list_only_shows_own_threads(auth_client) -> None:
  client, user = auth_client
  Thread.objects.create(user=user, title="mine")
  other = get_user_model().objects.create_user(username="other", password="x")
  Thread.objects.create(user=other, title="not mine")
  response = client.get("/chat/threads")
  titles = [t["title"] for t in response.data]
  assert titles == ["mine"]


@pytest.mark.django_db
@patch("chat.views.append_turn")
def test_send_message_returns_assistant_reply(mock_append, auth_client) -> None:
  client, user = auth_client
  thread = Thread.objects.create(user=user, title="t")
  from chat.models import Message

  mock_append.return_value = Message(
    thread=thread,
    role=Message.Role.ASSISTANT,
    content="hi",
  )
  response = client.post(
    f"/chat/threads/{thread.pk}/messages",
    {"content": "안녕"},
    format="json",
  )
  assert response.status_code == 201
  assert response.data["content"] == "hi"
  mock_append.assert_called_once()
