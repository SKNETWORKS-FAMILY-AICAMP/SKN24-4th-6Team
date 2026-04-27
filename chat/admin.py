from django.contrib import admin

from chat.models import Message, Thread


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
  list_display = ("id", "user", "title", "updated_at")
  search_fields = ("title", "user__username")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
  list_display = ("id", "thread", "role", "created_at")
  list_filter = ("role",)
