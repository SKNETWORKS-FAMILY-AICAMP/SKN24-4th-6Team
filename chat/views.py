from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from chat.models import Chatroom
from chat.serializers import (
  ChatSerializer,
  SendMessageSerializer,
  ChatroomSerializer,
)
from chat.services import AigoAIError, append_turn


class ChatroomListCreateView(generics.ListCreateAPIView):  # ThreadListCreateView → ChatroomListCreateView
  serializer_class = ChatroomSerializer                    # ThreadSerializer → ChatroomSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Chatroom.objects.filter(user_id=self.request.user)  # Thread → Chatroom

  def perform_create(self, serializer) -> None:
    serializer.save(user_id=self.request.user)


class ChatroomDetailView(generics.RetrieveDestroyAPIView):  # ThreadDetailView → ChatroomDetailView
  serializer_class = ChatroomSerializer                      # ThreadSerializer → ChatroomSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Chatroom.objects.filter(user_id=self.request.user).prefetch_related("chats")  # Thread → Chatroom, messages → chats


class SendMessageView(generics.GenericAPIView):
  serializer_class = SendMessageSerializer
  permission_classes = [IsAuthenticated]

  def post(self, request: Request, pk: int) -> Response:
    chatroom = generics.get_object_or_404(Chatroom, pk=pk, user_id=request.user)  # thread → chatroom, Thread → Chatroom
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
      assistant_message = append_turn(
        chatroom,
        user_content=serializer.validated_data["content"],
      )
    except AigoAIError as exc:
      return Response(
        {"detail": str(exc)},
        status=status.HTTP_502_BAD_GATEWAY,
      )

    return Response(
      ChatSerializer(assistant_message).data,  # MessageSerializer → ChatSerializer
      status=status.HTTP_201_CREATED,
    )
