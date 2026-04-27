import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_register_creates_user_and_returns_id() -> None:
  client = APIClient()
  response = client.post(
    "/api/auth/register",
    {"username": "newbie", "email": "n@example.com", "password": "longenough"},
    format="json",
  )
  assert response.status_code == 201
  assert "id" in response.data
  assert "password" not in response.data
  assert get_user_model().objects.filter(username="newbie").exists()


@pytest.mark.django_db
def test_register_rejects_short_password() -> None:
  client = APIClient()
  response = client.post(
    "/api/auth/register",
    {"username": "u", "password": "short"},
    format="json",
  )
  assert response.status_code == 400


@pytest.mark.django_db
def test_token_obtain_returns_access_and_refresh() -> None:
  get_user_model().objects.create_user(username="alice", password="longenough")
  client = APIClient()
  response = client.post(
    "/api/auth/token",
    {"username": "alice", "password": "longenough"},
    format="json",
  )
  assert response.status_code == 200
  assert "access" in response.data
  assert "refresh" in response.data


@pytest.mark.django_db
def test_token_obtain_rejects_bad_password() -> None:
  get_user_model().objects.create_user(username="bob", password="longenough")
  client = APIClient()
  response = client.post(
    "/api/auth/token",
    {"username": "bob", "password": "wrong"},
    format="json",
  )
  assert response.status_code == 401
