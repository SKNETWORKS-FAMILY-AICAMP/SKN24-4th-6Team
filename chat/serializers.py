from rest_framework import serializers

from chat.models import Message, Thread


class MessageSerializer(serializers.ModelSerializer):
  class Meta:
    model = Message
    fields = ("id", "thread", "role", "content", "created_at")
    read_only_fields = ("id", "thread", "role", "created_at")


class ThreadSerializer(serializers.ModelSerializer):
  messages = MessageSerializer(many=True, read_only=True)

  class Meta:
    model = Thread
    fields = ("id", "title", "created_at", "updated_at", "messages")
    read_only_fields = ("id", "created_at", "updated_at", "messages")


class SendMessageSerializer(serializers.Serializer):
  content = serializers.CharField()
