from unittest.mock import MagicMock, patch

import httpx
import pytest
from django.contrib.auth import get_user_model

from chat.models import Chat, Chatroom
from chat.services import stream_chat_turn


def _fake_stream_cm(status_code: int, lines: list[str]) -> MagicMock:
  """httpx.stream() 을 흉내내는 컨텍스트 매니저 mock"""
  response = MagicMock()
  response.status_code = status_code
  response.iter_lines.return_value = iter(lines)
  response.read.return_value = b""
  cm = MagicMock()
  cm.__enter__.return_value = response
  cm.__exit__.return_value = False
  return cm


@pytest.fixture
def user_with_room(db):
  """테스트용 사용자와 채팅방 생성"""
  user = get_user_model().objects.create_user(
    email="zed@example.com",
    nickname="zed",
    password="x",
  )
  room = Chatroom.objects.create(user_id=user, title="t")
  return user, room


@patch("aigo_ai.client.httpx.stream")
def test_stream_chat_turn_persists_user_and_assistant(mock_stream, user_with_room):
  """aigo-ai SSE 이벤트에 따라 user 메시지 저장 → token 이벤트마다 assistant 메시지 누적 → message_end 시 DB 저장 검증"""
  user, room = user_with_room
  mock_stream.return_value = _fake_stream_cm(
    200,
    [
      "event: token",
      'data: {"delta": "안녕"}',
      "",
      "event: token",
      'data: {"delta": "하세요"}',
      "",
      "event: message_end",
      'data: {"total_tokens": 5}',
      "",
    ],
  )

  emitted = b"".join(stream_chat_turn(room, user_content="질문", user_id=str(user.pk)))

  assert b"event: token" in emitted
  assert b"event: message_end" in emitted

  chats = list(room.chats.order_by("created_at").values_list("role", "content"))
  assert chats == [
    (Chat.Role.USER, "질문"),
    (Chat.Role.ASSISTANT, "안녕하세요"),
  ]


@patch("aigo_ai.client.httpx.stream")
def test_stream_chat_turn_upstream_http_error_yields_error_event(mock_stream, user_with_room):
  """aigo-ai SSE 스트림이 HTTP 200이 아닌 경우 error 이벤트를 yield 하고 assistant 메시지는 저장하지 않음"""
  user, room = user_with_room
  mock_stream.return_value = _fake_stream_cm(401, [])

  emitted = b"".join(stream_chat_turn(room, user_content="질문", user_id=str(user.pk)))

  assert b"event: error" in emitted
  roles = list(room.chats.values_list("role", flat=True))
  assert roles == [Chat.Role.USER]


@patch("aigo_ai.client.httpx.stream")
def test_stream_chat_turn_network_error_yields_error_event(mock_stream, user_with_room):
  """aigo-ai SSE 스트림에서 네트워크 오류 발생 시 error 이벤트를 yield 하고 assistant 메시지는 저장하지 않음"""
  user, room = user_with_room
  mock_stream.side_effect = httpx.ConnectError("boom")

  emitted = b"".join(stream_chat_turn(room, user_content="질문", user_id=str(user.pk)))

  assert b"UPSTREAM_NETWORK" in emitted
  roles = list(room.chats.values_list("role", flat=True))
  assert roles == [Chat.Role.USER]
