from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


class Message(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Text'
        IMAGE = 'image', 'Image'

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=MessageType.choices, default=MessageType.TEXT)
    media = models.ImageField(upload_to='messages/', blank=True, null=True,
                              validators=[FileExtensionValidator(allowed_extensions=['jpg','jpeg','png','gif'])])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sender', 'receiver', 'created_at'])
        ]

    def __str__(self) -> str:
        return f"Message({self.sender_id} -> {self.receiver_id}, {self.message_type})"

# Create your models here.
