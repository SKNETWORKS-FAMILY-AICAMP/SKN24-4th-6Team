import uuid
from collections.abc import Mapping
from contextlib import AbstractContextManager
from typing import Any

import httpx
from django.conf import settings


def _base_url() -> str:
  return settings.AIGO_AI_BASE_URL.rstrip("/")


def _headers(
  *,
  user_id: str | None,
  chatroom_id: str | None,
  accept: str | None = None,  # text/event-stream for SSE, application/json
) -> dict[str, str]:
  h: dict[str, str] = {}  # 헤더 생성
  api_key = settings.AIGO_AI_INTERNAL_API_KEY
  if api_key:
    h["X-Internal-Api-Key"] = api_key
  if user_id:
    h["X-User-Id"] = str(user_id)
  if chatroom_id:
    h["X-Chatroom-Id"] = str(chatroom_id)
  if accept:
    h["Accept"] = accept
  return h


def _timeout(read: float | None = None) -> httpx.Timeout:
  return httpx.Timeout(
    connect=10.0,
    read=read if read is not None else settings.AIGO_AI_REQUEST_TIMEOUT,
    write=10.0,
    pool=10.0,
  )


def stream(
  path: str,
  *,
  json_payload: Mapping[str, Any],
  user_id: str,
  chatroom_id: str | None = None,
) -> AbstractContextManager[httpx.Response]:
  """
  POST 채팅 스트리밍 요청
  with 블록 안에서 response.iter_bytes()로 SSE 바이트 프레임을 반복할 수 있는 컨텍스트 매니저 반환
  """
  return httpx.stream(
    "POST",
    f"{_base_url()}{path}",
    headers=_headers(
      user_id=user_id,
      chatroom_id=chatroom_id,
      accept="text/event-stream",
    ),
    json=dict(json_payload),
    timeout=_timeout(),
  )


def post_multipart(
  path: str,
  *,
  files: dict,
  user_id: str,
  chatroom_id: str | None = None,
  timeout: float | None = None,
) -> httpx.Response:
  """
  POST multipart/form-data 요청 (PDF 업로드)
  파일은 files={"file": (filename, file_bytes, content_type)} 형식으로 전달
  """
  return httpx.post(
    f"{_base_url()}{path}",
    headers={
      **_headers(user_id=user_id, chatroom_id=chatroom_id),
      "X-Idempotency-Key": str(uuid.uuid4()),
    },
    files=files,
    timeout=_timeout(read=timeout),
  )
