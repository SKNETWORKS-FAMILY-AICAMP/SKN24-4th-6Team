"""Business logic for chat: persist user/assistant turns and proxy to aigo-ai."""

from __future__ import annotations

import httpx
from django.conf import settings

from chat.models import Message, Thread


class AigoAIError(RuntimeError):
  """Raised when the upstream RAG service fails or returns malformed data."""


def ask_aigo_ai(question: str, *, timeout: float = 30.0) -> str:
  """Forward a single user question to the aigo-ai FastAPI service.

  Returns the assistant's answer as a plain string. Raises AigoAIError on any
  network or schema failure so callers can map it to a 502.
  """
  base_url = settings.AIGO_AI_BASE_URL.rstrip("/")
  try:
    response = httpx.post(
      f"{base_url}/chat",
      json={"question": question},
      timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
  except httpx.HTTPError as exc:
    raise AigoAIError(f"aigo-ai request failed: {exc}") from exc

  answer = data.get("answer")
  if not isinstance(answer, str):
    raise AigoAIError("aigo-ai response missing 'answer' field")
  return answer


def append_turn(thread: Thread, *, user_content: str) -> Message:
  """Persist a user message, call aigo-ai, persist the assistant reply.

  Returns the assistant Message. The user Message is also created as a side
  effect — caller can inspect via thread.messages.
  """
  Message.objects.create(thread=thread, role=Message.Role.USER, content=user_content)
  answer = ask_aigo_ai(user_content)
  return Message.objects.create(
    thread=thread,
    role=Message.Role.ASSISTANT,
    content=answer,
  )
