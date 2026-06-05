from django.contrib import admin
from chatbot.models import ChatSession, ChatMessage, Attachment


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "id"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "session", "role", "timestamp"]
    list_filter = ["role", "timestamp"]
    search_fields = ["content", "session__id"]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["id", "session", "file", "file_type", "uploaded_at"]
    list_filter = ["file_type", "uploaded_at"]
    search_fields = ["file"]
