from django.urls import path
from . import views

urlpatterns = [
    path('me/verify/', views.SelfVerifyView.as_view(), name='mypage-self-verify'),
    path('me/', views.MeView.as_view(), name='mypage-me'),
    path('me/password/', views.MePasswordView.as_view(), name='mypage-me-password'),
]
