from django.db import models
from accounts.models import User
from projects.models import Project


class Task(models.Model):

    class State(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_PROGRESS = "in_progress", "In Progress"
        IN_REVIEW = "in_review", "In Review"
        COMPLETED = "completed", "Completed"
        BLOCKED = "blocked", "Blocked"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    priority = models.BooleanField(default=False)

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="tasks"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_tasks"
    )
    last_updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="updated_tasks"
    )

    deadline = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title