from unittest.mock import patch

import httpx
import pytest
from django.contrib.auth import get_user_model

from chat.models import Message, Thread
from chat.services import AigoAIError, append_turn, ask_aigo_ai


@patch("chat.services.httpx.post")
def test_ask_aigo_ai_returns_answer_field(mock_post) -> None:
  mock_post.return_value = httpx.Response(
    200,
    json={"answer": "월세 5%까지 인상 가능합니다."},
    request=httpx.Request("POST", "http://example/chat"),
  )
  assert ask_aigo_ai("질문") == "월세 5%까지 인상 가능합니다."


@patch("chat.services.httpx.post")
def test_ask_aigo_ai_raises_on_http_error(mock_post) -> None:
  mock_post.side_effect = httpx.HTTPError("boom")
  with pytest.raises(AigoAIError):
    ask_aigo_ai("질문")


@patch("chat.services.httpx.post")
def test_ask_aigo_ai_raises_on_missing_answer(mock_post) -> None:
  mock_post.return_value = httpx.Response(
    200,
    json={"unrelated": "data"},
    request=httpx.Request("POST", "http://example/chat"),
  )
  with pytest.raises(AigoAIError):
    ask_aigo_ai("질문")


@pytest.mark.django_db
@patch("chat.services.ask_aigo_ai", return_value="답변입니다")
def test_append_turn_persists_user_and_assistant(mock_ai) -> None:
  user = get_user_model().objects.create_user(username="zed", password="x")
  thread = Thread.objects.create(user=user)
  assistant = append_turn(thread, user_content="질문")
  assert assistant.role == Message.Role.ASSISTANT
  assert assistant.content == "답변입니다"
  roles = list(thread.messages.values_list("role", flat=True))
  assert roles == [Message.Role.USER, Message.Role.ASSISTANT]
