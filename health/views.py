from django.http import HttpRequest, JsonResponse


def healthz(request: HttpRequest) -> JsonResponse:
  """Liveness probe. Always returns {"status": "ok"} when the process is up."""
  return JsonResponse({"status": "ok"})
