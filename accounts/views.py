import random
import string
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import User, EmailVerification
from .serializers import (
    EmailSendSerializer,
    EmailVerifySerializer,
    SignupSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    SelfVerifySerializer,
    ProfileUpdateSerializer,
    UserResponseSerializer,
)

# 6자리 문자전송
def generate_code(length=6):
    """6자리 영문 대문자 인증코드 생성"""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


# ================================================================
# 이메일 인증 공통
# ================================================================

class EmailVerificationView(APIView):
    """
    POST /auth/email-verification
    code 없음 → 인증코드 발송
    code 있음 → 인증코드 검증
    """
    permission_classes = [AllowAny]

    def post(self, request):
        if request.data.get('code'):
            serializer = EmailVerifySerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            verification = serializer.validated_data['verification']
            verification.is_verified = True
            verification.save()
            return Response({'message': '인증이 완료되었습니다.'}, status=status.HTTP_200_OK)

        serializer = EmailSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']
        code = generate_code()

        EmailVerification.objects.filter(email=email, purpose=purpose, is_verified=False).delete()
        EmailVerification.objects.create(
            email=email, code=code, purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=3),
        )
        send_mail(
            subject='[아이고청년] 이메일 인증 코드',
            message=f'인증 코드: {code}\n유효시간: 3분',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        return Response({'message': '인증코드가 발송되었습니다.'}, status=status.HTTP_200_OK)


class EmailSendView(APIView):
    """
    POST /api/users/email/send/
    인증코드 발송
    회원가입 (purpose=SIGNUP)
    비밀번호 재설정 (purpose=RESET)

    - 메일 발송 후 인증시간(3분) 동안 버튼 비활성화
    - 타이머 시작은 발송 시점 기준
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailSendSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']
        code = generate_code()

        # 기존 미완료 인증 레코드 무효화 (재발송 케이스)
        EmailVerification.objects.filter(
            email=email,
            purpose=purpose,
            is_verified=False,
        ).delete()

        EmailVerification.objects.create(
            email=email,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=3),
        )

        send_mail(
            subject='[아이고청년] 이메일 인증 코드',
            message=f'인증 코드: {code}\n유효시간: 3분',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response(
            {'message': '인증코드가 발송되었습니다.'},
            status=status.HTTP_200_OK
        )


class EmailVerifyView(APIView):
    """
    POST /api/users/email/verify/
    인증코드 검증
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 인증 완료 처리 → 회원가입/비밀번호 재설정 단계에서 확인용
        verification = serializer.validated_data['verification']
        verification.is_verified = True
        verification.save()

        return Response(
            {'message': '인증이 완료되었습니다.'},
            status=status.HTTP_200_OK
        )


# ================================================================
# 회원가입
# ================================================================

class SignupView(APIView):
    """
    POST /api/users/signup/

    플로우:
    1. EmailSendView → 인증코드 발송
    2. EmailVerifyView → 코드 검증 (is_verified=True)
    3. SignupView → 가입 완료 후 로그인 화면으로 이동
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        # 자동 로그인 없이 로그인 화면으로 리다이렉트
        return Response(
            {'message': '회원가입이 완료되었습니다. 로그인 해주세요.'},
            status=status.HTTP_201_CREATED
        )


# ================================================================
# 로그인 / 로그아웃
# ================================================================

class LoginView(APIView):
    """POST /api/users/login/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        if not User.objects.filter(email=email).exists():
            return Response(
                {'field': 'email', 'error': '등록되지 않은 이메일입니다.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response(
                {'field': 'password', 'error': '비밀번호가 올바르지 않습니다.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # django_session 테이블에 세션 생성, 응답 쿠키에 sessionid 포함
        login(request, user)

        # 로그인 성공 시 채팅화면으로 이동
        return Response(
            {'user': UserResponseSerializer(user).data},
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    POST /api/users/logout/

    로그아웃 확인창 → [로그아웃] 클릭 시 로그인 페이지로 이동
    logout()이 django_session 테이블에서 세션 즉시 삭제
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(
            {'message': '로그아웃 되었습니다.'},
            status=status.HTTP_200_OK
        )


# ================================================================
# 비밀번호 재설정
# ================================================================

class PasswordResetView(APIView):
    """
    POST /api/users/password/reset/

    플로우:
    1. EmailSendView (purpose=RESET) → 인증코드 발송
    2. EmailVerifyView → 코드 검증
    3. PasswordResetView → 새 비밀번호 저장
    변경 후 홈화면으로 이동
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        new_password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': '가입되지 않은 이메일 입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user.set_password(new_password)
        user.save()

        # 사용된 인증 레코드 삭제
        EmailVerification.objects.filter(
            email=email,
            purpose=EmailVerification.Purpose.RESET,
        ).delete()

        return Response(
            {'message': '비밀번호가 변경되었습니다.'},
            status=status.HTTP_200_OK
        )


# ================================================================
# 내정보 (본인인증 + 조회/수정/탈퇴)
# ================================================================

class SelfVerifyView(APIView):
    """
    POST /api/users/me/verify/

    - 사이드바 프로필 버튼 클릭 → 현재 비밀번호 입력 모달
    - 인증 성공 시 내정보 화면으로 이동
    - 비밀번호 미입력 시 확인 버튼 비활성화
    - 비밀번호 불일치 경고
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SelfVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        password = serializer.validated_data['password']

        # check_password: bcrypt 해시 검증
        if not request.user.check_password(password):
            return Response(
                {'error': '비밀번호가 일치하지 않습니다.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 세션에 본인인증 완료 플래그 저장
        # 내정보 화면 접근 시 이 플래그 확인
        request.session['self_verified'] = True

        return Response(
            {'message': '본인인증이 완료되었습니다.'},
            status=status.HTTP_200_OK
        )


class MePasswordView(APIView):
    """PUT /api/user/me/password — 로그인 상태에서 비밀번호 변경"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.set_password(serializer.validated_data['password'])
        user.save()
        logout(request)

        return Response({'message': '비밀번호가 변경되었습니다.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    GET  /api/users/me/      → 내정보 조회
    PATCH /api/users/me/     → 닉네임/비밀번호 수정
    DELETE /api/users/me/    → 회원탈퇴
    """
    permission_classes = [IsAuthenticated]

    def _check_self_verified(self, request):
        """
        세션에 self_verified 플래그가 없으면 접근 차단
        """
        if not request.session.get('self_verified'):
            return Response(
                {'error': '본인인증이 필요합니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def get(self, request):
        """
        닉네임, 이메일 표시
        이메일은 수정 불가 (가입 시 등록된 이메일 고정)
        """
        error = self._check_self_verified(request)
        if error:
            return error

        return Response(
            UserResponseSerializer(request.user).data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        """
        수정하기 버튼
        - 닉네임 변경 후 → 채팅방으로 이동
        - 비밀번호 변경 후 → 로그인 화면으로 이동
        변경 타입을 응답에 포함 → 프론트에서 리다이렉트 분기
        """
        error = self._check_self_verified(request)
        if error:
            return error

        serializer = ProfileUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        changed = []

        if serializer.validated_data.get('nickname'):
            user.nickname = serializer.validated_data['nickname']
            changed.append('nickname')

        if serializer.validated_data.get('password'):
            user.set_password(serializer.validated_data['password'])
            changed.append('password')
            # 비밀번호 변경 후 기존 세션 무효화 → 로그인 화면으로 이동
            logout(request)

        user.save()

        return Response(
            {
                'message': '수정되었습니다.',
                'changed': changed,
                # 프론트 리다이렉트 분기용
                # nickname → /chat, password → /login
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        """
        회원탈퇴 팝업 → [탈퇴하기]      
        회원정보 및 채팅 기록 삭제 후 홈화면으로 이동
        CASCADE 설정으로 chatroom → chat, contract 등 연쇄 삭제
        """
        error = self._check_self_verified(request)
        if error:
            return error

        user = request.user
        logout(request)
        # ON DELETE CASCADE → chatroom → chat, contract → property_info 순 삭제
        user.delete()

        return Response(
            {'message': '탈퇴가 완료되었습니다.'},
            status=status.HTTP_200_OK
        )
