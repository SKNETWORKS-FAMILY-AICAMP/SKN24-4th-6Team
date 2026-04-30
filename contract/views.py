import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Contract, PropertyInfo
from django.shortcuts import render

# Create your views here.

@require_http_methods(['POST'])                                             # POST 요청만 허용
def upload_contract(request, chatroom_id):                                  # URL에서 어느 채팅방(chatroom_id)의 계약서인지 받기
    
    # Step 1. 
    # 파일 존재 여부 확인
    if 'file' not in request.FILES:                                         # 
        return JsonResponse({'success': False, 'message': '파일이 없습니다'}, status=400)
    # 파일이 존재한다면
    file = request.FILES['file']

    # 5MB 용량 체크
    if file.size > 5 * 1024 * 1024:                                         # file.size는 단위가 바이트이므로, 5MB를 바이트로 변환하여 초과 여부 검출 
        return JsonResponse({'success': False, 'message': '파일은 최대 5MB까지 업로드 가능합니다'}, status=400)

    # PDF 형식 체크
    if not file.name.endswith('.pdf'):                                      # 확장자가 pdf가 맞는지 확인
        return JsonResponse({'success': False, 'message': 'PDF 파일만 업로드 가능합니다'}, status=400)

    # FastAPI AI 서버로 파일 바이트 전송 및 예외 상황 처리
    try:
        response = requests.post(
            settings.INFER_URL,                                             # config의 settings.py에 있는 FastAPI 서버 주소
            files={'file': (file.name, file.read(), 'application/pdf')},    # 
            timeout=settings.INFER_TIMEOUT                                  # config의 settings.py에 있는 timeout 값
        )
        result = response.json()
    except requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'message': 'AI 서버 응답 시간 초과'}, status=504)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'AI 서버 오류'}, status=500)

    # Contract 생성/업데이트
    contract, _ = Contract.objects.update_or_create(                        # chatroom_id의 계약서가 있으면 수정, 없으면 생성
        chatroom_id=chatroom_id,
        defaults={
            'title': file.name,
            'content': result.get('content'),
            'size': file.size,
        }
    )

    # PropertyInfo 생성/업데이트
    PropertyInfo.objects.update_or_create(
        contract=contract,
        defaults={
            'location': result.get('location'),
            'period': result.get('period'),
            'month_rent': result.get('month_rent'),
            'security': result.get('security'),
            'house_cost': result.get('house_cost'),
        }
    )

    return JsonResponse({'success': True, 'message': '계약서 분석이 완료되었습니다'})