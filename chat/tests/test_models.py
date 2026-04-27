import pytest
from django.contrib.auth import get_user_model

from chat.models import Message, Thread


@pytest.mark.django_db
def test_thread_str_uses_title_when_set() -> None:
  user = get_user_model().objects.create_user(username="alice", password="x")
  thread = Thread.objects.create(user=user, title="lease question")
  assert str(thread) == "lease question"


@pytest.mark.django_db
def test_thread_str_falls_back_to_pk_when_title_blank() -> None:
  user = get_user_model().objects.create_user(username="bob", password="x")
  thread = Thread.objects.create(user=user)
  assert str(thread) == f"Thread {thread.pk}"


@pytest.mark.django_db
def test_message_ordering_is_chronological() -> None:
  user = get_user_model().objects.create_user(username="carol", password="x")
  thread = Thread.objects.create(user=user, title="t")
  first = Message.objects.create(thread=thread, role=Message.Role.USER, content="q1")
  second = Message.objects.create(thread=thread, role=Message.Role.ASSISTANT, content="a1")
  assert list(thread.messages.all()) == [first, second]
