import json
import logging
from collections.abc import Callable, Iterator
from typing import Any

import httpx

from aigo_ai import client

logger = logging.getLogger(__name__)


def _emit(event: str, data: dict[str, Any]) -> bytes:
  """
  SSE 형식으로 이벤트 이름과 JSON 데이터 직렬화하여 바이트로 반환
  """
  payload = json.dumps(data, ensure_ascii=False)
  return f"event: {event}\ndata: {payload}\n\n".encode()


def stream_chat(
  *,
  query: str,
  history: list[dict[str, str]],
  user_id: str,
  chatroom_id: str | None = None,
  contract_context: dict | None = None,
  on_event: Callable[[str, dict], None] | None = None,
) -> Iterator[bytes]:
  """
  aigo-ai /chat/stream 엔드포인트에 SSE 채팅 요청을 보내고, 원시 SSE 바이트 프레임을 반복하여 반환
  """
  payload = {
    "query": query,
    "history": history,
    "contract_context": contract_context,
  }

  buffer_event: str | None = None
  buffer_data: list[str] = []

  try:
    with client.stream(
      "/chat/stream",
      json_payload=payload,
      user_id=user_id,
      chatroom_id=chatroom_id,
    ) as response:
      # HTTP 오류 응답 처리
      # 400 이상은 클라이언트/서버 오류로 간주하여 에러 이벤트를 yield 하고 스트리밍 종료
      if response.status_code >= 400:
        body = response.read().decode("utf-8", errors="replace")[:500]
        logger.warning("[aigo-ai] upstream error %s: %s", response.status_code, body)
        yield _emit(
          "error",
          {
            "code": "UPSTREAM_HTTP",
            "message": f"[aigo-ai] HTTP {response.status_code}",
          },
        )
        return

      for line in response.iter_lines():
        # 빈 줄은 이벤트 구분자. buffer_event가 None이 아니면 이벤트 완성으로 간주하여 처리
        if line == "":
          if buffer_event is None:
            buffer_data = []
            continue

          data_text = "\n".join(buffer_data)
          # JSON 데이터 파싱. 실패해도 이벤트는 처리하되 data_obj는 빈 dict로
          try:
            data_obj = json.loads(data_text) if data_text else {}
          except json.JSONDecodeError:
            data_obj = {}

          if on_event:
            on_event(buffer_event, data_obj)

          yield _emit(buffer_event, data_obj)

          # "message_end" 또는 "error" 이벤트가 발생하면 스트리밍 종료
          if buffer_event in ("message_end", "error"):
            return

          buffer_event = None
          buffer_data = []
          continue

        # SSE 필드 처리: "event:"로 시작하면 이벤트 이름 설정, "data:"로 시작하면 데이터 라인 추가
        if line.startswith(":"):
          continue
        if line.startswith("event:"):
          buffer_event = line[len("event:") :].strip()
        elif line.startswith("data:"):
          buffer_data.append(line[len("data:") :].lstrip())

  except httpx.NetworkError as e:
    # ConnectError / ReadError / WriteError / CloseError 등 네트워크 계층 실패
    logger.error("[aigo-ai] network error: %s", str(e))
    yield _emit(
      "error",
      {
        "code": "UPSTREAM_NETWORK",
        "message": f"[aigo-ai] network error: {str(e)}",
      },
    )
  except httpx.RequestError as e:
    logger.error("[aigo-ai] request error: %s", str(e))
    yield _emit(
      "error",
      {
        "code": "UPSTREAM_REQUEST",
        "message": f"[aigo-ai] request error: {str(e)}",
      },
    )
