from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class MypagePageView(LoginRequiredMixin, TemplateView):
  """마이페이지 HTML 뷰"""
  template_name = "mypage/mypage.html"

from accounts.serializers import UserResponseSerializer
from .serializers import SelfVerifySerializer, ProfileUpdateSerializer


class SelfVerifyView(APIView):
    """
    POST /api/mypage/me/verify/

    - 사이드바 프로필 버튼 클릭 → 현재 비밀번호 입력 모달
    - 인증 성공 시 내정보 화면으로 이동
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SelfVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(serializer.validated_data['password']):
            return Response(
                {'error': '비밀번호가 일치하지 않습니다.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        request.session['self_verified'] = True

        return Response(
            {'message': '본인인증이 완료되었습니다.'},
            status=status.HTTP_200_OK
        )


class MeView(APIView):
    """
    GET    /api/mypage/me/  → 내정보 조회
    PATCH  /api/mypage/me/  → 닉네임/비밀번호 수정
    DELETE /api/mypage/me/  → 회원탈퇴
    """
    permission_classes = [IsAuthenticated]

    def _check_self_verified(self, request):
        if not request.session.get('self_verified'):
            return Response(
                {'error': '본인인증이 필요합니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def get(self, request):
        error = self._check_self_verified(request)
        if error:
            return error

        return Response(
            UserResponseSerializer(request.user).data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
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
            logout(request)

        user.save()

        return Response(
            {
                'message': '수정되었습니다.',
                'changed': changed,
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        """
        회원탈퇴 — CASCADE로 chatroom → chat, contract 연쇄 삭제
        """
        error = self._check_self_verified(request)
        if error:
            return error

        user = request.user
        logout(request)
        user.delete()

        return Response(
            {'message': '탈퇴가 완료되었습니다.'},
            status=status.HTTP_200_OK
        )


class MePasswordView(APIView):
    """PUT /api/mypage/me/password/ — 로그인 상태에서 비밀번호 변경"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        from accounts.serializers import PasswordResetSerializer
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.set_password(serializer.validated_data['password'])
        user.save()
        logout(request)

        return Response({'message': '비밀번호가 변경되었습니다.'}, status=status.HTTP_200_OK)
