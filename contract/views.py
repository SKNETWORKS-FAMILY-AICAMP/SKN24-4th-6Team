import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from aigo_ai import analyze_pdf
from aigo_ai.errors import AigoAIError
from chat.models import Chatroom

from .models import Contract, PropertyInfo

logger = logging.getLogger(__name__)


@login_required()
@require_http_methods(["POST"])
def upload_contract(request, chatroom_id):
  # Step 0. 채팅방 유저와 조작자가 일치하는지 확인
  if not Chatroom.objects.filter(chatroom_id=chatroom_id, user_id=request.user).exists():
    return JsonResponse({"success": False, "message": "권한이 없습니다"}, status=403)

  # Step 1. 파일 검증
  if "file" not in request.FILES:
    return JsonResponse({"success": False, "message": "파일이 없습니다"}, status=400)
  file = request.FILES["file"]
  if file.size > 5 * 1024 * 1024:
    return JsonResponse(
      {"success": False, "message": "파일은 최대 5MB까지 업로드 가능합니다"}, status=400
    )
  if not file.name.endswith(".pdf"):
    return JsonResponse({"success": False, "message": "PDF 파일만 업로드 가능합니다"}, status=400)

  # Step 2. FastaAPI AI 서버로 파일 바이트 전송 및 예외 상황 처리
  try:
    result = analyze_pdf(
      filename=file.name,
      file_bytes=file.read(),
      user_id=str(request.user.pk),
      chatroom_id=str(chatroom_id),
    )
  except AigoAIError as exc:
    logger.warning("aigo-ai pdf/analyze 실패: %s", exc)
    return JsonResponse({"success": False, "message": "AI 서버 오류"}, status=502)

  confidence = result.get("confidence", None)

  # TODO: if success (200번대):
  # 테이블 정보가 있는 생성

  # Step 3. Contract(테이블) & PropertyInfo(테이블) 생성/업데이트
  # [Contract Table]
  Contract.objects.filter(
    chatroom_id=chatroom_id
  ).delete()  # 1. 기존 Contract 레코드 삭제 (연결된 PropertyInfo도 자동 삭제)
  contract = Contract.objects.create(  # 2. 새 Contract 생성 (새로운 contract_id 발급)
    chatroom_id=chatroom_id,
    title=file.name,
    content=result.get("content", ""),
    size=file.size,
  )
  # [PropertyInfo Table]: 새로운 PDF를 올리면, contract_id만 담긴 빈 테이블이 우선 생성됨.
  PropertyInfo.objects.create(contract=contract)

  return JsonResponse(
    {
      "success": True,
      "message": "계약서 분석이 완료되었습니다",
      "confidence": confidence,  # AI 서버가 반환한 신뢰도 값
      "low_confidence": confidence is not None and confidence < 0.85,  # 85% 미만 여부
    }
  )


@login_required()
@require_http_methods(["GET"])
def get_contract(request, chatroom_id):

  if not Chatroom.objects.filter(chatroom_id=chatroom_id, user_id=request.user).exists():
    return JsonResponse({"success": False, "message": "권한이 없습니다"}, status=403)

  try:
    contract = Contract.objects.get(chatroom_id=chatroom_id)
    property_info = PropertyInfo.objects.get(contract=contract)

    return JsonResponse(
      {
        "success": True,
        "contract": {
          "title": contract.title,
          "content": contract.content,
          "size": contract.size,
        },
        "property_info": {
          "location": property_info.location,
          "start_date": str(property_info.start_date),
          "end_date": str(property_info.end_date),
          "month_rent": property_info.month_rent,
          "deposit": property_info.deposit,
          "house_cost": property_info.house_cost,
        },
      }
    )
  except Contract.DoesNotExist:
    return JsonResponse({"success": False, "message": "계약서 정보가 없습니다"}, status=404)


@login_required()
@require_http_methods(["POST"])
def update_property(request, chatroom_id):

  if not Chatroom.objects.filter(chatroom_id=chatroom_id, user_id=request.user).exists():
    return JsonResponse({"success": False, "message": "권한이 없습니다"}, status=403)

  try:
    contract = Contract.objects.get(chatroom_id=chatroom_id)
    property_info = PropertyInfo.objects.get(contract=contract)

    property_info.location = request.POST.get("location", property_info.location)
    property_info.start_date = request.POST.get("period", property_info.start_date)
    property_info.end_date = request.POST.get("period", property_info.end_date)
    property_info.month_rent = request.POST.get("month_rent", property_info.month_rent)
    property_info.deposit = request.POST.get("deposit", property_info.deposit)
    property_info.house_cost = request.POST.get("house_cost", property_info.house_cost)
    property_info.save()

    return JsonResponse({"success": True, "message": "매물 정보가 수정되었습니다"})
  except Contract.DoesNotExist:
    return JsonResponse({"success": False, "message": "계약서 정보가 없습니다"}, status=404)


@login_required()
@require_http_methods(["POST"])
def update_terms(request, chatroom_id):

  if not Chatroom.objects.filter(chatroom_id=chatroom_id, user_id=request.user).exists():
    return JsonResponse({"success": False, "message": "권한이 없습니다"}, status=403)

  try:
    contract = Contract.objects.get(chatroom_id=chatroom_id)
    contract.content = request.POST.get("content", contract.content)
    contract.save()
    return JsonResponse({"success": True, "message": "특약 정보가 수정되었습니다"})
  except Contract.DoesNotExist:
    return JsonResponse({"success": False, "message": "계약서 정보가 없습니다"}, status=404)
