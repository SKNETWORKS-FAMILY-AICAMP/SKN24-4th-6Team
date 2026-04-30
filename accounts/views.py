from rest_framework import generics
from rest_framework.permissions import AllowAny

from accounts.serializers import UserCreateSerializer


class RegisterView(generics.CreateAPIView):
  """POST /api/auth/register — anonymous signup, returns the new user."""

  serializer_class = UserCreateSerializer
  permission_classes = [AllowAny]
