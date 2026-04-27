from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
  """Custom user stub. Locked in early so AUTH_USER_MODEL is set before the
  first migration — swapping later requires a destructive reset."""

  pass
