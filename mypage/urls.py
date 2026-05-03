from django.urls import path

from mypage import views

app_name = "mypage"

urlpatterns = [
  path("", views.MypagePageView.as_view(), name="mypage-page"),
]
