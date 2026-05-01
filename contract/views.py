import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Contract, PropertyInfo
from chat.models import Chatroom
import logging

# Create your views here.

@login_required()                                                           # settings.py에서 LOGIN_URL을 설정했으면 이렇게 두고, 아니라면 login_url = ''
@require_http_methods(['POST'])                                             # POST 요청만 허용
def upload_contract(request, chatroom_id):                                  # URL에서 어느 채팅방(chatroom_id)의 계약서인지 받기
                                                                            # 문제: 피그마 상에서는 채팅방 생성 화면에서 pdf를 받을 수 있게 되어있는데, 현재 정의한 함수에서는 chatroom_id를 무조건 받게 되어있다는 점
                                                                                    # -> 이렇게 되면 채팅방 생성 화면에서는 pdf 업로드를 막거나 : 사용자 편의만 보면 이 방향으로 가기도 애매함.
                                                                                    # -> 채팅방 생성 화면에서 pdf를 올리는 그 순간 chatroom_id도 만들어지게 하거나 : 그럼 query 일절 없이 pdf를 올린 채팅방에 대한 취급을 별개로 처리해줘야 해서 로직이 복잡해짐.
                                                                                    # -> 채팅방 생성 누르면 채팅방 id 부여: 흠.. 지지해질 거 같은데 지지해...

    # Step 0. 채팅방 유저와 조작자가 일치하는지를 확인
    if not Chatroom.objects.filter(chatroom_id=chatroom_id, user_id=request.user).exists():
        return JsonResponse({'success': False, 'message': '권한이 없습니다'}, status=403)
    
    # Step 1. 파일 검증
    # 파일 존재 여부 확인
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'message': '파일이 없습니다'}, status=400)
    # 파일이 존재하는 경우 file 객체 선언
    file = request.FILES['file']
    # 5MB 용량 체크
    if file.size > 5 * 1024 * 1024:                                         # file.size는 단위가 바이트이므로, 5MB를 바이트로 변환하여 초과 여부 검출 
        return JsonResponse({'success': False, 'message': '파일은 최대 5MB까지 업로드 가능합니다'}, status=400)
    # PDF 형식 체크
    if not file.name.endswith('.pdf'):                                      # 확장자가 pdf가 맞는지 확인
        return JsonResponse({'success': False, 'message': 'PDF 파일만 업로드 가능합니다'}, status=400)


    # Step 2. FastAPI AI 서버로 파일 바이트 전송 및 예외 상황 처리
    try:
        response = requests.post(
            settings.INFER_URL,                                             # config의 settings.py에 있는 FastAPI 서버 주소
            files={'file': (file.name, file.read(), 'application/pdf')},
            # timeout=settings.INFER_TIMEOUT                                  # config의 settings.py에 있는 timeout 값 # TODO: 타임아웃 설정하실 겁니까?
        )
        result = response.json()
    except requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'message': 'AI 서버 응답 시간 초과'}, status=504)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f'AI 서버 오류: {e}')
        return JsonResponse({'success': False, 'message': 'AI 서버 오류'}, status=500)

    confidence = result.get('confidence', None)

    # TODO: if success (200번대):
        # 테이블 정보가 있는 생성


    # Step 3. Contract(테이블) & PropertyInfo(테이블) 생성/업데이트
    # [Contract Table]
    Contract.objects.filter(chatroom_id=chatroom_id).delete()                   # 1. 기존 Contract 레코드 삭제 (연결된 PropertyInfo도 자동 삭제)
    contract = Contract.objects.create(                                         # 2. 새 Contract 생성 (새로운 contract_id 발급)
        chatroom_id=chatroom_id,
        title=file.name,
        content=result.get('content', ''),
        size=file.size,
    )
    # [PropertyInfo Table]: 새로운 PDF를 올리면, contract_id만 담긴 빈 테이블이 우선 생성됨.
    PropertyInfo.objects.create(contract=contract)

    return JsonResponse({
        'success': True,
        'message': '계약서 분석이 완료되었습니다',
        'confidence': confidence,                    # AI 서버가 반환한 신뢰도 값
        'low_confidence': confidence is not None and confidence < 0.85  # 85% 미만 여부
    })



@login_required()
@require_http_methods(['GET'])
def get_contract(request, chatroom_id):

    if not Chatroom.objects.filter(chatroom_id=chatroom_id, user_id=request.user).exists():
        return JsonResponse({'success': False, 'message': '권한이 없습니다'}, status=403)

    try:
        contract = Contract.objects.get(chatroom_id=chatroom_id)
        property_info = PropertyInfo.objects.get(contract=contract)

        return JsonResponse({
            'success': True,
            'contract': {
                'title': contract.title,
                'content': contract.content,
                'size': contract.size,
            },
            'property_info': {
                'location': property_info.location,
                'period': property_info.period,
                'month_rent': property_info.month_rent,
                'security': property_info.security,
                'house_cost': property_info.house_cost,
            }
        })
    except Contract.DoesNotExist:
        return JsonResponse({'success': False, 'message': '계약서가 없습니다'}, status=404)
    


@login_required() 
@require_http_methods(['POST'])
def update_property(request, chatroom_id):

    if not Chatroom.objects.filter(chatroom_id=chatroom_id, user_id=request.user).exists():
        return JsonResponse({'success': False, 'message': '권한이 없습니다'}, status=403)

    try:
        contract = Contract.objects.get(chatroom_id=chatroom_id)
        property_info = PropertyInfo.objects.get(contract=contract)

        property_info.location = request.POST.get('location', property_info.location)
        property_info.period = request.POST.get('period', property_info.period)
        property_info.month_rent = request.POST.get('month_rent', property_info.month_rent)
        property_info.security = request.POST.get('security', property_info.security)
        property_info.house_cost = request.POST.get('house_cost', property_info.house_cost)
        property_info.save()

        return JsonResponse({'success': True, 'message': '매물 정보가 수정되었습니다'})
    except Contract.DoesNotExist:
        return JsonResponse({'success': False, 'message': '계약서가 없습니다'}, status=404)