import pytest
from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import EmailVerification, User

BASE = "/api/users"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def signup_verification(db):
    return EmailVerification.objects.create(
        email="new@example.com",
        code="123456",
        purpose=EmailVerification.Purpose.SIGNUP,
        is_verified=True,
        expires_at=timezone.now() + timedelta(minutes=3),
    )


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        email="test@example.com",
        nickname="테스터",
        password="Test1234!",
    )
    u.is_verified = True
    u.save()
    return u


# ── 이메일 발송 ──────────────────────────────────────────────────

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.django_db
def test_email_send_signup_success(client):
    res = client.post(f"{BASE}/email/send/", {"email": "new@example.com", "purpose": "SIGNUP"}, format="json")
    assert res.status_code == 200
    assert EmailVerification.objects.filter(email="new@example.com", purpose="SIGNUP").exists()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.django_db
def test_email_send_signup_rejects_existing_email(client, user):
    res = client.post(f"{BASE}/email/send/", {"email": user.email, "purpose": "SIGNUP"}, format="json")
    assert res.status_code == 400


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.django_db
def test_email_send_reset_rejects_unknown_email(client):
    res = client.post(f"{BASE}/email/send/", {"email": "ghost@example.com", "purpose": "RESET"}, format="json")
    assert res.status_code == 400


# ── 이메일 인증 ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_email_verify_success(client):
    EmailVerification.objects.create(
        email="new@example.com",
        code="654321",
        purpose=EmailVerification.Purpose.SIGNUP,
        is_verified=False,
        expires_at=timezone.now() + timedelta(minutes=3),
    )
    res = client.post(f"{BASE}/email/verify/", {"email": "new@example.com", "code": "654321", "purpose": "SIGNUP"}, format="json")
    assert res.status_code == 200
    assert EmailVerification.objects.get(email="new@example.com").is_verified is True


@pytest.mark.django_db
def test_email_verify_wrong_code(client):
    EmailVerification.objects.create(
        email="new@example.com",
        code="654321",
        purpose=EmailVerification.Purpose.SIGNUP,
        is_verified=False,
        expires_at=timezone.now() + timedelta(minutes=3),
    )
    res = client.post(f"{BASE}/email/verify/", {"email": "new@example.com", "code": "000000", "purpose": "SIGNUP"}, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_email_verify_expired(client):
    EmailVerification.objects.create(
        email="new@example.com",
        code="654321",
        purpose=EmailVerification.Purpose.SIGNUP,
        is_verified=False,
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    res = client.post(f"{BASE}/email/verify/", {"email": "new@example.com", "code": "654321", "purpose": "SIGNUP"}, format="json")
    assert res.status_code == 400


# ── 회원가입 ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_signup_success(client, signup_verification):
    res = client.post(f"{BASE}/", {
        "email": "new@example.com",
        "password": "Test1234!",
        "password_confirm": "Test1234!",
        "nickname": "신규유저",
    }, format="json")
    assert res.status_code == 201
    assert User.objects.filter(email="new@example.com").exists()


@pytest.mark.django_db
def test_signup_without_verification(client):
    res = client.post(f"{BASE}/", {
        "email": "unverified@example.com",
        "password": "Test1234!",
        "password_confirm": "Test1234!",
        "nickname": "미인증",
    }, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_signup_password_mismatch(client, signup_verification):
    res = client.post(f"{BASE}/", {
        "email": "new@example.com",
        "password": "Test1234!",
        "password_confirm": "Different1!",
        "nickname": "유저",
    }, format="json")
    assert res.status_code == 400


# ── 로그인 / 로그아웃 ─────────────────────────────────────────────

@pytest.mark.django_db
def test_login_success(client, user):
    res = client.post(f"{BASE}/login/", {"email": user.email, "password": "Test1234!"}, format="json")
    assert res.status_code == 200
    assert "user" in res.data


@pytest.mark.django_db
def test_login_wrong_password(client, user):
    res = client.post(f"{BASE}/login/", {"email": user.email, "password": "WrongPass1!"}, format="json")
    assert res.status_code == 401


@pytest.mark.django_db
def test_logout_success(client, user):
    client.force_login(user)
    res = client.post(f"{BASE}/logout/")
    assert res.status_code == 200


@pytest.mark.django_db
def test_logout_requires_auth(client):
    res = client.post(f"{BASE}/logout/")
    assert res.status_code == 403


# ── 비밀번호 재설정 ───────────────────────────────────────────────

@pytest.mark.django_db
def test_password_reset_success(client, user):
    EmailVerification.objects.create(
        email=user.email,
        code="999999",
        purpose=EmailVerification.Purpose.RESET,
        is_verified=True,
        expires_at=timezone.now() + timedelta(minutes=3),
    )
    res = client.post(f"{BASE}/password/reset/", {
        "email": user.email,
        "password": "NewPass1234!",
        "password_confirm": "NewPass1234!",
    }, format="json")
    assert res.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NewPass1234!")


# ── 내정보 ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_me_requires_self_verify(client, user):
    client.force_login(user)
    res = client.get("/api/mypage/me/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_me_get_after_self_verify(client, user):
    client.force_login(user)
    session = client.session
    session["self_verified"] = True
    session.save()
    res = client.get("/api/mypage/me/")
    assert res.status_code == 200
    assert res.data["email"] == user.email
