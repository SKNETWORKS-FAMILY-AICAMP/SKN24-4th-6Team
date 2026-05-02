from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from chat.models import Chatroom


@pytest.fixture
def auth_client(db):
  """인증된 APIClient와 해당 사용자 반환"""
  user = get_user_model().objects.create_user(
    email="dana@example.com",
    nickname="dana",
    password="x",
  )
  client = APIClient()
  client.force_authenticate(user=user)
  return client, user


def test_unauthenticated_chatroom_list_blocked(db) -> None:
  """인증되지 않은 사용자는 채팅방 목록 API 접근 불가"""
  client = APIClient()
  response = client.get("/api/v1/chatrooms")
  # SessionAuthentication + IsAuthenticated → 401 또는 403
  assert response.status_code in (401, 403)


def test_create_chatroom_assigns_current_user(auth_client) -> None:
  """채팅방 생성 시 현재 사용자가 user_id 로 저장되는지 검증"""
  client, user = auth_client
  response = client.post("/api/v1/chatrooms", {"title": "t1"}, format="json")
  assert response.status_code == 201
  assert Chatroom.objects.get(pk=response.data["chatroom_id"]).user_id == user


def test_chatroom_list_only_shows_own_rooms(auth_client) -> None:
  """사용자는 자신의 채팅방 목록만 조회할 수 있는지 검증"""
  client, user = auth_client
  Chatroom.objects.create(user_id=user, title="mine")
  other = get_user_model().objects.create_user(
    email="other@example.com", nickname="oth", password="x"
  )
  Chatroom.objects.create(user_id=other, title="not mine")
  response = client.get("/api/v1/chatrooms")
  titles = [r["title"] for r in response.data]
  assert titles == ["mine"]


@patch("chat.views.stream_chat_turn")
def test_send_message_returns_event_stream(mock_stream, auth_client) -> None:
  """메시지 전송 시 stream_chat_turn() 의 결과를 SSE 형식으로 반환하는지 검증"""
  client, user = auth_client
  room = Chatroom.objects.create(user_id=user, title="t")

  mock_stream.return_value = iter(
    [
      b'event: token\ndata: {"delta": "hi"}\n\n',
      b"event: message_end\ndata: {}\n\n",
    ]
  )

  response = client.post(
    f"/api/v1/chatrooms/{room.pk}/messages",
    {"content": "안녕"},
    format="json",
  )

  assert response.status_code == 200
  assert response["Content-Type"].startswith("text/event-stream")
  body = b"".join(response.streaming_content)
  assert b"event: token" in body
  mock_stream.assert_called_once()
