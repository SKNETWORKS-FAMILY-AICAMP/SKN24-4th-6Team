import re
from django.utils import timezone
from rest_framework import serializers
from core.models import User, EmailVerification


# ----------------------------------------------------------------
# 공통 검증 함수
# ----------------------------------------------------------------

def validate_password_format(value):
    """
    비밀번호: 영문, 숫자, 특수문자 중 2종 이상 포함, 8~16자
    """
    if not (8 <= len(value) <= 16):
        raise serializers.ValidationError('비밀번호 형식이 올바르지 않습니다.')

    has_alpha = bool(re.search(r'[a-zA-Z]', value))
    has_digit = bool(re.search(r'[0-9]', value))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', value))

    # 2종 이상 포함 여부 체크
    if sum([has_alpha, has_digit, has_special]) < 2:
        raise serializers.ValidationError('비밀번호 형식이 올바르지 않습니다.')

    return value


def validate_nickname_format(value):
    """
    닉네임: 한글, 영문, 숫자 포함 2~6자
    """
    if not re.match(r'^[가-힣a-zA-Z0-9]{2,6}$', value):
        raise serializers.ValidationError('닉네임 형식이 올바르지 않습니다.')
    return value


# ----------------------------------------------------------------
# 이메일 인증 관련
# ----------------------------------------------------------------

class EmailSendSerializer(serializers.Serializer):
    """
    인증코드 발송 요청
    """
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=EmailVerification.Purpose.choices)

    def validate(self, attrs):
        email = attrs['email']
        purpose = attrs['purpose']

        if purpose == EmailVerification.Purpose.SIGNUP:
            # 이미 가입된 이메일 경고
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    {'email': '이미 가입된 이메일입니다.'}
                )
        elif purpose == EmailVerification.Purpose.RESET:
            # 가입되지 않은 이메일 경고
            if not User.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    {'email': '가입되지 않은 이메일 입니다.'}
                )
        return attrs


class EmailVerifySerializer(serializers.Serializer):
    """
    인증코드 검증 요청
    """
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=EmailVerification.Purpose.choices)

    def validate(self, attrs):
        try:
            verification = EmailVerification.objects.filter(
                email=attrs['email'],
                purpose=attrs['purpose'],
                is_verified=False,
            ).latest('created_at')
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError(
                {'code': '인증코드가 일치하지 않습니다.'}
            )

        # 타이머 만료 처리
        if verification.is_expired():
            raise serializers.ValidationError(
                {'code': '인증시간이 만료 되었습니다.'}
            )

        # 코드 불일치
        if verification.code != attrs['code']:
            raise serializers.ValidationError(
                {'code': '인증코드가 일치하지 않습니다.'}
            )

        attrs['verification'] = verification
        return attrs


# ----------------------------------------------------------------
# 회원가입
# ----------------------------------------------------------------

class SignupSerializer(serializers.Serializer):
    """
    인증 완료된 이메일로만 가입 가능
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    nickname = serializers.CharField(max_length=6)

    def validate_email(self, value):
        # 이미 가입된 이메일 재확인
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('이미 가입된 이메일입니다.')

        # 이메일 인증 완료 여부 확인
        if not EmailVerification.objects.filter(
            email=value,
            purpose=EmailVerification.Purpose.SIGNUP,
            is_verified=True
        ).exists():
            raise serializers.ValidationError('이메일 인증이 완료되지 않았습니다.')

        return value

    def validate_password(self, value):
        return validate_password_format(value)

    def validate_nickname(self, value):
        return validate_nickname_format(value)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': '비밀번호가 일치하지 않습니다.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            nickname=validated_data['nickname'],
            password=validated_data['password'],
        )
        user.is_verified = True
        user.save()
        return user


# ----------------------------------------------------------------
# 로그인
# ----------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    """
    로그인
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# ----------------------------------------------------------------
# 비밀번호 재설정
# ----------------------------------------------------------------

class PasswordResetSerializer(serializers.Serializer):
    """
    비밀번호 재설정
    이메일 인증 완료 후 새 비밀번호 설정
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value):
        # 인증 완료 여부 확인
        if not EmailVerification.objects.filter(
            email=value,
            purpose=EmailVerification.Purpose.RESET,
            is_verified=True
        ).exists():
            raise serializers.ValidationError('이메일 인증이 완료되지 않았습니다.')
        return value

    def validate_password(self, value):
        return validate_password_format(value)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': '비밀번호가 일치하지 않습니다.'}
            )
        return attrs


# ----------------------------------------------------------------
# 본인인증
# ----------------------------------------------------------------

class SelfVerifySerializer(serializers.Serializer):
    """
    본인인증 모달
    내정보 접근 전 현재 비밀번호 확인
    """
    password = serializers.CharField(write_only=True)


# ----------------------------------------------------------------
# 내정보 수정
# ----------------------------------------------------------------

class ProfileUpdateSerializer(serializers.Serializer):
    """
    닉네임, 비밀번호 중 하나 이상 변경 시 수정하기 버튼 활성화
    """
    nickname = serializers.CharField(max_length=6, required=False)
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)

    def validate_nickname(self, value):
        return validate_nickname_format(value)

    def validate_password(self, value):
        return validate_password_format(value)

    def validate(self, attrs):
        # 변경 항목이 아무것도 없는 경우
        if not attrs.get('nickname') and not attrs.get('password'):
            raise serializers.ValidationError('변경할 항목이 없습니다.')

        # 비밀번호 변경 시 확인 필드도 필수
        if attrs.get('password'):
            if not attrs.get('password_confirm'):
                raise serializers.ValidationError(
                    {'password_confirm': '새 비밀번호 확인을 입력해주세요.'}
                )
            # 설계서 SCR-USER-007 항목 4-1
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError(
                    {'password_confirm': '비밀번호가 일치하지 않습니다.'}
                )
        return attrs


# ----------------------------------------------------------------
# 응답 전용
# ----------------------------------------------------------------

class UserResponseSerializer(serializers.ModelSerializer):
    """
    응답 전용: 민감 정보(password) 제외
    """
    class Meta:
        model = User
        fields = ['user_id', 'email', 'nickname', 'is_verified', 'created_at']
