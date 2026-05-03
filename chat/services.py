import logging
from collections.abc import Iterator

from aigo_ai import stream_chat
from aigo_ai.errors import AigoAIError
from chat.models import Chat, Chatroom

logger = logging.getLogger(__name__)

_HISTORY_LIMIT = 20

__all__ = ["AigoAIError", "stream_chat_turn"]


def _build_history(chatroom: Chatroom) -> list[dict]:
  """최근 메시지를 aigo-ai history 포맷으로 변환"""
  recent = list(chatroom.chats.order_by("-created_at").values("role", "content")[:_HISTORY_LIMIT])
  return [
    {"role": row["role"], "content": row["content"] or ""}
    for row in reversed(recent)
    if row["role"] in {Chat.Role.USER, Chat.Role.ASSISTANT}
  ]


def _persist_assistant(chatroom: Chatroom, content: str) -> None:
  """assistant 메시지를 DB에 저장"""
  if not content:
    return
  Chat.objects.create(
    chatroom_id=chatroom,
    role=Chat.Role.ASSISTANT,
    content=content,
  )
  chatroom.save(update_fields=["last_chat_at"])


def stream_chat_turn(
  chatroom: Chatroom,
  *,
  user_content: str,
  user_id: str,
) -> Iterator[bytes]:
  """user 메시지를 즉시 저장 → aigo-ai SSE 를 그대로 yield → message_end 시 assistant 저장"""
  Chat.objects.create(
    chatroom_id=chatroom,
    role=Chat.Role.USER,
    content=user_content,
  )

  history = _build_history(chatroom)
  tokens: list[str] = []
  completed = False

  # aigo-ai SSE 이벤트 핸들러
  def _on_event(event: str, data: dict) -> None:
    nonlocal completed
    if event == "token":
      delta = data.get("delta")
      if isinstance(delta, str):
        tokens.append(delta)
    elif event == "message_end":
      completed = True

  yield from stream_chat(
    query=user_content,
    history=history[:-1],
    user_id=str(user_id),
    chatroom_id=str(chatroom.chatroom_id),
    on_event=_on_event,
  )

  if completed:
    _persist_assistant(chatroom, "".join(tokens))
