import logging
from typing import Any

import httpx

from aigo_ai import client
from aigo_ai.errors import AigoAIError

logger = logging.getLogger(__name__)


def analyze_pdf(
  *,
  filename: str,
  file_bytes: bytes,
  user_id: str,
  chatroom_id: str | None = None,
  timeout: float = 60.0,
) -> dict[str, Any]:
  """
  PDF 파일을 aigo-ai /pdf/analyze 엔드포인트로 전송하여 분석 결과를 JSON으로 반환
  """
  try:
    response = client.post_multipart(
      "/pdf/analyze",
      files={"file": (filename, file_bytes, "application/pdf")},
      user_id=user_id,
      chatroom_id=chatroom_id,
      timeout=timeout,
    )
  except httpx.HTTPError as exc:
    logger.exception("[aigo-ai] pdf/analyze transport failed")
    raise AigoAIError(f"[aigo-ai] pdf/analyze failed: {exc}") from exc

  if response.status_code >= 400:
    logger.warning(
      "[aigo-ai] pdf/analyze HTTP %s: %s",
      response.status_code,
      response.text[:300],
    )
    raise AigoAIError(f"[aigo-ai] pdf/analyze HTTP {response.status_code}")

  try:
    return response.json()
  except ValueError as exc:
    raise AigoAIError(f"[aigo-ai] pdf/analyze returned non-JSON: {exc}") from exc
