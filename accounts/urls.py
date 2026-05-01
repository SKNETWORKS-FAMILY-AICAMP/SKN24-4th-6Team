# apps/users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 이메일 인증 공통

    path('email/send/', views.EmailSendView.as_view(), name='email-send'),
    path('email/verify/', views.EmailVerifyView.as_view(), name='email-verify'),

    # 회원가입

    path('signup/', views.SignupView.as_view(), name='signup'),

    # 로그인 / 로그아웃

    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # 비밀번호 재설정

    path('password/reset/', views.PasswordResetView.as_view(), name='password-reset'),

    # 본인인증

    path('me/verify/', views.SelfVerifyView.as_view(), name='self-verify'),

    # 내정보

    path('me/', views.MeView.as_view(), name='me'),
]

