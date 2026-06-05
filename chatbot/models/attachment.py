from django.db import models
from chatbot.models.chat_session import ChatSession


class Attachment(models.Model):
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="chatbot_attachments/")
    file_type = models.CharField(max_length=10)  # pdf, docx, txt, md
    parsed_text = models.TextField(blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.id} ({self.file_type}) for Session {self.session.id}"
