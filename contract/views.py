import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Contract, PropertyInfo
from django.shortcuts import render

# Create your views here.

# TODO : @ 로그인권한 추가
@require_http_methods(['POST'])                                             # POST 요청만 허용
def upload_contract(request, chatroom_id):                                  # URL에서 어느 채팅방(chatroom_id)의 계약서인지 받기
    
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
            timeout=settings.INFER_TIMEOUT                                  # config의 settings.py에 있는 timeout 값
        )
        result = response.json()
    except requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'message': 'AI 서버 응답 시간 초과'}, status=504)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'AI 서버 오류'}, status=500)
        # TODO: raise http으로 변경 권장

    # TODO: if success (200번대):
        # 테이블 정보가 있는 생성


    # Step 3. Contract(테이블) & PropertyInfo(테이블) 생성/업데이트
    # 아래 두 방식 모두 일단 Contract 테이블의 새로운 항목이 추가되면 contract_id만 담긴 빈 테이블을 생성
    # 이 방식이 비효율적이라 판단되면, 사용자가 직접 테이블을 작성하고 저장 버튼을 누를 때 append 되도록 해도 될 것 같긴 함 >>> TODO: 방법론 검색해보기

    # 방법 1.
    # [Contract Table] : .update_or_create()를 사용한 케이스 - 이 방식은 contract_id를 바꿀 수 없다는 치명적인 단점이 있다. (Contract의 PK가 contract_id라서...)
    # contract, _ = Contract.objects.update_or_create(                        # 기존 chatroom_id의 계약서가 있으면 수정, 없으면 생성
    #     chatroom_id=chatroom_id,
    #     defaults={
    #         'title': file.name,
    #         'content': result.get('content'),
    #         'size': file.size,
    #     }
    # )
    # [PropertyInfo Table] : contract_id가 바뀌지 않아서 기존 PropertyInfo 레코드가 유지되므로, 새 PDF를 업로드해도 이전에 사용자가 입력한 매물 정보가 초기화되지 않음 > 수정은 가능함.
    # PropertyInfo.objects.update_or_create(contract=contract)

    # 방법 2. 방법 1의 단점 보완
    # [Contract Table]
    Contract.objects.filter(chatroom_id=chatroom_id).delete()                   # 1. 기존 Contract 레코드 삭제 (연결된 PropertyInfo도 자동 삭제)
    contract = Contract.objects.create(                                         # 2. 새 Contract 생성 (새로운 contract_id 발급)
        chatroom_id=chatroom_id,
        title=file.name,
        content=result.get('content'),
        size=file.size,
    )
    # [PropertyInfo Table]
    PropertyInfo.objects.create(contract=contract)

    return JsonResponse({'success': True, 'message': '계약서 분석이 완료되었습니다'})



# TODO : @ 로그인권한 추가
@require_http_methods(['GET'])
def get_contract(request, chatroom_id):
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
    


# TODO : @ 로그인권한 추가
@require_http_methods(['POST'])
def update_property(request, chatroom_id):
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