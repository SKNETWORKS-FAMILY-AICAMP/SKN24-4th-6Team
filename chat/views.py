from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from chat.models import Thread
from chat.serializers import (
  MessageSerializer,
  SendMessageSerializer,
  ThreadSerializer,
)
from chat.services import AigoAIError, append_turn


class ThreadListCreateView(generics.ListCreateAPIView):
  """GET /chat/threads — list current user's threads. POST — create a new thread."""

  serializer_class = ThreadSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Thread.objects.filter(user=self.request.user)

  def perform_create(self, serializer) -> None:
    serializer.save(user=self.request.user)


class ThreadDetailView(generics.RetrieveDestroyAPIView):
  """GET /chat/threads/<id> — fetch one thread + its messages."""

  serializer_class = ThreadSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Thread.objects.filter(user=self.request.user).prefetch_related("messages")


class SendMessageView(generics.GenericAPIView):
  """POST /chat/threads/<id>/messages — send a user turn, get an assistant reply."""

  serializer_class = SendMessageSerializer
  permission_classes = [IsAuthenticated]

  def post(self, request: Request, pk: int) -> Response:
    thread = generics.get_object_or_404(Thread, pk=pk, user=request.user)
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
      assistant_message = append_turn(
        thread,
        user_content=serializer.validated_data["content"],
      )
    except AigoAIError as exc:
      return Response(
        {"detail": str(exc)},
        status=status.HTTP_502_BAD_GATEWAY,
      )

    return Response(
      MessageSerializer(assistant_message).data,
      status=status.HTTP_201_CREATED,
    )
