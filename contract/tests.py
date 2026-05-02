import uuid
import io
import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from chat.models import Chatroom
from .models import Contract, PropertyInfo



User = get_user_model()

class ContractTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            nickname='테스터'
        )
        self.chatroom = Chatroom.objects.create(user_id=self.user)
        self.chatroom_id = self.chatroom.chatroom_id
        self.client.login(email='test@test.com', password='testpass123')

    # ── TC-13: PDF 업로드 → OCR → SCR-CHAT-003 계약서 정보 확인 ──
    @patch('contract.views.httpx.post')
    def test_TC13_upload_pdf_success(self, mock_post):
        """
        Happy Path
        PDF 업로드 → AI 서버 OCR 처리 → Contract, PropertyInfo 생성 확인
        """
        mock_post.return_value.json.return_value = {
            'content': '계약서 내용입니다',
        }
        pdf_file = io.BytesIO(b'%PDF-1.4 fake pdf content')
        pdf_file.name = 'test.pdf'

        response = self.client.post(
            f'/contract/{self.chatroom_id}/upload/',
            {'file': pdf_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Contract 생성 확인
        self.assertTrue(Contract.objects.filter(chatroom_id=self.chatroom_id).exists())
        # PropertyInfo 빈 테이블 생성 확인
        contract = Contract.objects.get(chatroom_id=self.chatroom_id)
        self.assertTrue(PropertyInfo.objects.filter(contract=contract).exists())

    # ── TC-25: PDF 아닌 파일 업로드 시 오류 ──
    def test_TC25_upload_not_pdf(self):
        """
        Error Path
        .jpg/.docx 등 PDF 아닌 파일 업로드 시 오류 메시지 반환
        """
        jpg_file = io.BytesIO(b'fake jpg content')
        jpg_file.name = 'test.jpg'

        response = self.client.post(
            f'/contract/{self.chatroom_id}/upload/',
            {'file': jpg_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('PDF', data['message'])

    # ── TC-26: 5MB 초과 PDF 업로드 시 오류 ──
    def test_TC26_upload_over_5mb(self):
        """
        Error Path
        5MB 초과 PDF 업로드 시 오류 메시지 반환
        """
        big_file = io.BytesIO(b'0' * (5 * 1024 * 1024 + 1))
        big_file.name = 'big.pdf'

        response = self.client.post(
            f'/contract/{self.chatroom_id}/upload/',
            {'file': big_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('5MB', data['message'])

    # ── TC-27: OCR 신뢰도 낮은 경우 (Edge Case) ──
    @patch('contract.views.httpx.post')
    def test_TC27_low_ocr_confidence(self, mock_post):
        """
        Edge Case
        낮은 화질 PDF → AI 서버가 낮은 신뢰도 응답 반환 시 처리 확인
        현재는 AI 서버 응답을 그대로 저장하므로 업로드는 성공
        → 신뢰도 경고는 프론트엔드에서 처리
        """
        mock_post.return_value.json.return_value = {
            'content': '일부만 인식된 내용...',
            'confidence': 0.6,  # 85% 미만
        }
        pdf_file = io.BytesIO(b'%PDF-1.4 low quality scan')
        pdf_file.name = 'low_quality.pdf'

        response = self.client.post(
            f'/contract/{self.chatroom_id}/upload/',
            {'file': pdf_file},
            format='multipart'
        )
        # 백엔드는 업로드 성공 처리 (신뢰도 경고는 프론트 담당)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    # ── TC-28: 계약서 매핑 정보(매물 정보) 수정 확인 ──
    def test_TC28_update_property_success(self):
        """
        Happy Path
        SCR-CHAT-003 매핑 정보 수정 → DB 반영 확인
        """
        contract = Contract.objects.create(
            chatroom_id=self.chatroom_id,
            title='test.pdf',
            content='계약서 내용',
            size=1024,
        )
        PropertyInfo.objects.create(contract=contract)

        response = self.client.post(
            f'/contract/{self.chatroom_id}/property/',
            {
                'location': '서울시 마포구 XX로 XX길',
                'start_date': '2025-03-01',
                'end_date': '2027-02-28',
                'month_rent': 80,
                'deposit': 15000,
                'house_cost': '별도 정산',
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # DB 반영 확인
        property_info = PropertyInfo.objects.get(contract=contract)
        self.assertEqual(property_info.location, '서울시 마포구 XX로 XX길')
        self.assertEqual(property_info.month_rent, 80)
        self.assertEqual(property_info.deposit, 15000)
        self.assertEqual(property_info.house_cost, '별도 정산')

    # ── TC-28 연장: 특약 정보 수정 확인 ──
    def test_TC28_update_property_partial(self):
        """
        Happy Path
        일부 필드만 수정 시 나머지 기존 값 유지 확인
        """
        contract = Contract.objects.create(
            chatroom_id=self.chatroom_id,
            title='test.pdf',
            content='계약서 내용',
            size=1024,
        )
        PropertyInfo.objects.create(
            contract=contract,
            location='서울시 강남구',
            month_rent=100,
        )

        # location만 수정
        response = self.client.post(
            f'/contract/{self.chatroom_id}/property/',
            {'location': '서울시 마포구'}
        )
        self.assertEqual(response.status_code, 200)

        # location만 바뀌고 month_rent는 유지 확인
        property_info = PropertyInfo.objects.get(contract=contract)
        self.assertEqual(property_info.location, '서울시 마포구')
        self.assertEqual(property_info.month_rent, 100)  # 기존 값 유지

    # ── TC-29: PII 마스킹 확인 ──
    @patch('contract.views.httpx.post')
    def test_TC29_pii_masking(self, mock_post):
        """
        Happy Path
        PII 포함 PDF 업로드 시 AI 서버가 마스킹 처리된 내용 반환
        → DB에 마스킹된 내용 저장 확인
        """
        mock_post.return_value.json.return_value = {
            'content': '임대인: ***\n주민번호: ***-*******\n연락처: ***-****-****',
        }
        pdf_file = io.BytesIO(b'%PDF-1.4 pii content')
        pdf_file.name = 'pii_contract.pdf'

        response = self.client.post(
            f'/contract/{self.chatroom_id}/upload/',
            {'file': pdf_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)

        # 마스킹된 내용이 저장됐는지 확인
        contract = Contract.objects.get(chatroom_id=self.chatroom_id)
        self.assertIn('***', contract.content)
        self.assertNotIn('주민번호: 901201-1234567', contract.content)

    # ── 권한 없는 유저 접근 (공통) ──
    def test_unauthorized_upload(self):
        """
        Error Path
        다른 유저가 채팅방에 PDF 업로드 시도 시 403 반환
        """
        other_user = User.objects.create_user(
            email='other@test.com',
            password='otherpass123',
            nickname='다른유저'
        )
        self.client.login(email='other@test.com', password='otherpass123')

        pdf_file = io.BytesIO(b'%PDF-1.4 fake pdf content')
        pdf_file.name = 'test.pdf'

        response = self.client.post(
            f'/contract/{self.chatroom_id}/upload/',
            {'file': pdf_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 403)

    # ── 로그인 없이 접근 ──
    def test_login_required(self):
        """
        Error Path
        비로그인 상태에서 접근 시 리다이렉트 확인
        """
        self.client.logout()
        pdf_file = io.BytesIO(b'%PDF-1.4 fake pdf content')
        pdf_file.name = 'test.pdf'

        response = self.client.post(
            f'/contract/{self.chatroom_id}/upload/',
            {'file': pdf_file},
            format='multipart'
        )
        # login_required → 로그인 페이지로 리다이렉트
        self.assertEqual(response.status_code, 302)