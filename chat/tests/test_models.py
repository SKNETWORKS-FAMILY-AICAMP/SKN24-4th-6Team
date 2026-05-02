import pytest
from django.contrib.auth import get_user_model

from chat.models import Chat, Chatroom


@pytest.fixture
def user(db):
  return get_user_model().objects.create_user(
    email="alice@example.com",
    nickname="alice",
    password="x",
  )


def test_chatroom_str_uses_title_when_set(user):
  room = Chatroom.objects.create(user_id=user, title="lease question")
  assert str(room) == "lease question"


def test_chatroom_str_falls_back_to_pk_when_title_blank(user):
  room = Chatroom.objects.create(user_id=user, title="")
  assert str(room) == f"Chatroom {room.pk}"


def test_chat_ordering_is_chronological(user):
  room = Chatroom.objects.create(user_id=user, title="t")
  first = Chat.objects.create(chatroom_id=room, role=Chat.Role.USER, content="q1")
  second = Chat.objects.create(chatroom_id=room, role=Chat.Role.ASSISTANT, content="a1")
  assert list(room.chats.all()) == [first, second]
