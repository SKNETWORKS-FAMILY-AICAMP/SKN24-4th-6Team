from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import StreamingHttpResponse
from django.views.generic import TemplateView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BaseRenderer
from rest_framework.request import Request

from chat.models import Chatroom
from chat.serializers import (
  ChatroomSerializer,
  SendMessageSerializer,
)
from chat.services import stream_chat_turn


class SSERenderer(BaseRenderer):
  media_type = "text/event-stream"
  format = "sse"
  charset = "utf-8"

  def render(self, data, accepted_media_type=None, renderer_context=None):
    return b""


class ChatPageView(LoginRequiredMixin, TemplateView):
  """채팅 페이지. URL 에 chatroom_id 가 있으면 해당 방을 활성 상태로 렌더"""

  template_name = "chat/chat.html"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    chatrooms = Chatroom.objects.filter(user_id=self.request.user)
    context["chatrooms"] = chatrooms
    context["chatroom_count"] = chatrooms.count()
    context["current_chatroom_id"] = kwargs.get("chatroom_id")
    return context


class ChatroomListCreateView(generics.ListCreateAPIView):
  """채팅방 목록 조회 및 생성"""

  serializer_class = ChatroomSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Chatroom.objects.filter(user_id=self.request.user)

  def perform_create(self, serializer) -> None:
    serializer.save(user_id=self.request.user)


class ChatroomDetailView(generics.RetrieveDestroyAPIView):
  """채팅방 상세 조회 및 삭제 (삭제 시 해당 채팅방의 모든 메시지도 삭제)"""

  serializer_class = ChatroomSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Chatroom.objects.filter(user_id=self.request.user).prefetch_related("chats")


class SendMessageView(generics.GenericAPIView):
  """메시지 전송 및 SSE 스트리밍 응답"""

  serializer_class = SendMessageSerializer
  permission_classes = [IsAuthenticated]
  renderer_classes = [SSERenderer]

  def post(self, request: Request, pk: int) -> StreamingHttpResponse:
    chatroom = generics.get_object_or_404(Chatroom, pk=pk, user_id=request.user)
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    response = StreamingHttpResponse(
      stream_chat_turn(
        chatroom,
        user_content=serializer.validated_data["content"],
        user_id=request.user.pk,
      ),
      content_type="text/event-stream",
    )
    # SSE 는 실시간성이 중요하므로 캐싱 방지 및 버퍼링 해제 헤더 추가
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
