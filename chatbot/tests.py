from django.test import TestCase
from django.contrib.auth import get_user_model
from chatbot.models import ChatSession, ChatMessage, Attachment
from chatbot.serializers import ChatSessionSerializer, AttachmentUploadSerializer

User = get_user_model()


class ChatbotModelsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123", email="test@example.com"
        )
        self.session = ChatSession.objects.create(user=self.user)

    def test_chat_session_creation(self):
        self.assertEqual(self.session.user, self.user)
        self.assertIsNone(self.session.title)
        self.assertTrue(ChatSession.objects.filter(id=self.session.id).exists())

    def test_chat_message_creation(self):
        message = ChatMessage.objects.create(
            session=self.session, role=ChatMessage.Role.USER, content="Hello Agent"
        )
        self.assertEqual(message.session, self.session)
        self.assertEqual(message.role, ChatMessage.Role.USER)
        self.assertEqual(message.content, "Hello Agent")


class ChatbotSerializersTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser2", password="testpassword123"
        )
        self.session = ChatSession.objects.create(user=self.user)

    def test_chat_session_serializer(self):
        serializer = ChatSessionSerializer(instance=self.session)
        data = serializer.data
        self.assertEqual(data["id"], str(self.session.id))
        self.assertIsNone(data["title"])
        self.assertEqual(len(data["messages"]), 0)

    def test_attachment_upload_validation(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Test valid PDF upload serialization
        valid_pdf = SimpleUploadedFile(
            "document.pdf", b"pdf content", content_type="application/pdf"
        )
        data = {"session": self.session.id, "file": valid_pdf}
        serializer = AttachmentUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        attachment = serializer.save()
        self.assertEqual(attachment.file_type, "pdf")

        # Test valid DOCX upload serialization
        valid_docx = SimpleUploadedFile(
            "document.docx",
            b"docx content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        data_docx = {"session": self.session.id, "file": valid_docx}
        serializer_docx = AttachmentUploadSerializer(data=data_docx)
        self.assertTrue(serializer_docx.is_valid(), serializer_docx.errors)
        attachment_docx = serializer_docx.save()
        self.assertEqual(attachment_docx.file_type, "docx")

        # Test invalid file type (e.g. png)
        invalid_png = SimpleUploadedFile(
            "document.png", b"image content", content_type="image/png"
        )
        data_invalid = {"session": self.session.id, "file": invalid_png}
        serializer_invalid = AttachmentUploadSerializer(data=data_invalid)
        self.assertFalse(serializer_invalid.is_valid())
        self.assertIn("file", serializer_invalid.errors)
