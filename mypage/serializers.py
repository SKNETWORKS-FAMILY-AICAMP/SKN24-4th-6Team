from rest_framework import serializers
from accounts.serializers import validate_password_format, validate_nickname_format


class SelfVerifySerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)


class ProfileUpdateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=6, required=False)
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)

    def validate_nickname(self, value):
        return validate_nickname_format(value)

    def validate_password(self, value):
        return validate_password_format(value)

    def validate(self, attrs):
        if not attrs.get('nickname') and not attrs.get('password'):
            raise serializers.ValidationError('변경할 항목이 없습니다.')

        if attrs.get('password'):
            if not attrs.get('password_confirm'):
                raise serializers.ValidationError(
                    {'password_confirm': '새 비밀번호 확인을 입력해주세요.'}
                )
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError(
                    {'password_confirm': '비밀번호가 일치하지 않습니다.'}
                )
        return attrs
