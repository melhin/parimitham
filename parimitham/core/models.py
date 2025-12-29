from django.db import models
from django.utils import timezone


class DocumentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    FAILURE = "failure", "Failure"


class Document(models.Model):
    # File location will be stored in the FileField
    file = models.FileField(upload_to="documents/")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.PENDING)

    def __str__(self):
        return f"Document {self.id} - {self.status}"

    class Meta:
        ordering = ["-created_at"]
