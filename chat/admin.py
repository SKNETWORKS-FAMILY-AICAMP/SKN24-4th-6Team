from django.contrib import admin
from chat.models import Chat, Chatroom

# Django 관리자 페이지(/admin)에서 모델을 어떻게 보여줄지 설정하는 파일

@admin.register(Chatroom)   # Chatroom 모델을 관리자 페이지에 등록
class ChatroomAdmin(admin.ModelAdmin):
  list_display = ("chatroom_id", "user_id", "title", "has_contract", "last_chat_at", "created_at")  # 목록 화면에서 보여줄 컬럼
  search_fields = ("title", "has_contract", "user_id__username")                                    # 검색 기능에서 검색할 필드


@admin.register(Chat)       # Chat 모델을 관리자 페이지에 등록
class ChatAdmin(admin.ModelAdmin):
  list_display = ("chat_id", "chatroom_id", "role", "content", "created_at")
  list_filter = ("role",)
