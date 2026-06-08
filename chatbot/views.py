from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ChatSession, ChatMessage, Attachment
from .serializers import (
    ChatSessionSerializer,
    ChatSessionCreateSerializer,
    SendMessageSerializer,
    AttachmentUploadSerializer,
)
from .services.db_agent import run_db_agent
from .services.document_agent import run_document_agent, process_attachment
from .services.llm_service import generate_response


class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ChatSessions, uploading attachments, and sending messages."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only access their own chat sessions
        return ChatSession.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ChatSessionCreateSerializer
        elif self.action == "message":
            return SendMessageSerializer
        elif self.action == "attachments":
            return AttachmentUploadSerializer
        return ChatSessionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def message(self, request, pk=None):
        """Sends a user message, routes it to the Document Agent (if attachments exist)
        or the DB Agent (if no attachments exist), handles dynamic title generation,
        saves both messages in history, and returns the chat session history.
        """
        session = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_content = serializer.validated_data["content"]

        # 1. Save user message to database
        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content=user_content
        )

        # 2. Dynamic Title Generation (on the first message)
        if not session.title:
            try:
                title_prompt = (
                    "Create a short chat title summarizing this user message. "
                    "Max 5 words. Do not use quotes.\n\n"
                    f"User message: {user_content}\n\n"
                    "Title:"
                )
                generated_title = generate_response(title_prompt).strip()
                # Clean up quotes if returned by LLM
                generated_title = (
                    generated_title.replace('"', "").replace("'", "").strip()
                )
                session.title = generated_title[:255]
                session.save()
            except Exception:
                pass

        # 3. Route to Document Agent (if attachments exist) or DB Agent (if not)
        response_text = ""
        if session.attachments.exists():
            try:
                response_text = run_document_agent(user_content, session.id)
            except Exception as e:
                response_text = f"Error executing Document Agent: {str(e)}"
        else:
            try:
                response_text = run_db_agent(user_content, request.user.id, session_id=session.id)
            except Exception as e:
                response_text = f"Error executing DB Agent: {str(e)}"

        # 4. Save assistant reply to database
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=response_text,
        )

        # 5. Return updated session history
        return Response(
            ChatSessionSerializer(session).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def attachments(self, request, pk=None):
        """Uploads an attachment (PDF, DOCX, TXT, MD) for this chat session,
        extracts text, generates embeddings, and indexes it.
        """
        session = self.get_object()

        # Build request data with session ID set
        data = request.data.copy()
        data["session"] = session.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save()

        # Trigger processing of attachment
        result = process_attachment(attachment.id)

        if "error" in result:
            attachment.delete()  # Clean up database entry if parsing fails
            return Response(
                {"error": f"Failed to process and index attachment: {result['error']}"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(
            {
                "message": "Attachment uploaded and indexed successfully.",
                "attachment": AttachmentUploadSerializer(attachment).data,
                "chunks_indexed": result.get("num_chunks", 0),
            },
            status=status.HTTP_201_CREATED,
        )
