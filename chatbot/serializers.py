from rest_framework import serializers
from .models import ChatSession, ChatMessage, Attachment


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "timestamp"]
        read_only_fields = ["id", "role", "timestamp"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at", "updated_at", "messages"]
        read_only_fields = ["id", "title", "created_at", "updated_at"]


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """Lightweight serializer used only for session creation."""

    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at"]
        read_only_fields = ["id", "title", "created_at"]


class SendMessageSerializer(serializers.Serializer):
    """Validates the incoming message payload for the /message/ endpoint."""

    content = serializers.CharField(min_length=1, max_length=4096)


class AttachmentUploadSerializer(serializers.ModelSerializer):
    """Handles uploading files (PDF, DOCX, TXT, MD) and dynamically determines their type."""

    class Meta:
        model = Attachment
        fields = ["id", "session", "file", "file_type", "uploaded_at"]
        read_only_fields = ["id", "file_type", "uploaded_at"]

    def validate_file(self, value):
        name = value.name.lower()
        valid_extensions = (".pdf", ".docx", ".txt", ".md")
        if not name.endswith(valid_extensions):
            raise serializers.ValidationError(
                "Only PDF (.pdf), Word (.docx), Plain Text (.txt), and Markdown (.md) files are allowed."
            )
        return value

    def create(self, validated_data):
        file_obj = validated_data["file"]
        ext = file_obj.name.lower().split(".")[-1]
        validated_data["file_type"] = ext
        return super().create(validated_data)