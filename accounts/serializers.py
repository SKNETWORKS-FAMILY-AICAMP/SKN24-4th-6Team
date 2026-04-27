from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserCreateSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True, min_length=8)

  class Meta:
    model = get_user_model()
    fields = ("id", "username", "email", "password")
    read_only_fields = ("id",)

  def create(self, validated_data: dict) -> object:
    return get_user_model().objects.create_user(**validated_data)
