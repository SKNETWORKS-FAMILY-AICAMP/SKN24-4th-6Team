from rest_framework import serializers
from chat.models import Chatroom, Chat


class ChatSerializer(serializers.ModelSerializer):
  class Meta:
    model = Chat
    fields = ("chat_id", "chatroom_id", "role", "content", "created_at")
    read_only_fields = ("chat_id", "chatroom_id", "role", "created_at")


class ChatroomSerializer(serializers.ModelSerializer):
  chats = ChatSerializer(many=True, read_only=True)   # 채팅방 조회 시 메시지 목록도 중첩해서 함께 반환

  class Meta:
    model = Chatroom
    fields = ("chatroom_id", "title", "created_at", "last_chat_at", "chats")
    read_only_fields = ("chatroom_id", "created_at", "last_chat_at", "chats")


class SendMessageSerializer(serializers.Serializer):  # 메시지 전송 시 요청 body의 content 값만 받아서 검증
  content = serializers.CharField()
