from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
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


# class ChatPageView(LoginRequiredMixin, TemplateView):
class ChatPageView(TemplateView):
  template_name = "chat/chat.html"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    chatrooms = Chatroom.objects.filter(user_id=self.request.user)
    context["chatrooms"] = chatrooms
    context["chatroom_count"] = chatrooms.count()
    return context


class ChatroomListCreateView(generics.ListCreateAPIView):
  serializer_class = ChatroomSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Chatroom.objects.filter(user_id=self.request.user)

  def perform_create(self, serializer) -> None:
    serializer.save(user_id=self.request.user)


class ChatroomDetailView(generics.RetrieveDestroyAPIView):
  serializer_class = ChatroomSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Chatroom.objects.filter(user_id=self.request.user).prefetch_related("chats")


class SendMessageView(generics.GenericAPIView):
  serializer_class = SendMessageSerializer
  permission_classes = [IsAuthenticated]

  def post(self, request: Request, pk: int) -> Response:
    chatroom = generics.get_object_or_404(Chatroom, pk=pk, user_id=request.user)
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
      ChatSerializer(assistant_message).data,
      status=status.HTTP_201_CREATED,
    )