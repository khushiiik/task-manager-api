from django.db import models
from django.contrib.auth.models import AbstractUser
from teams.models import Team


class User(AbstractUser):

    class Role(models.TextChoices):
        QA = "qa", "QA"
        MANAGER = "manager", "Manager"
        ADMIN = "admin", "Admin"
        DEVELOPER = "developer", "Developer"

    role = models.CharField(max_length=20, choices=Role.choices, null=True, blank=True)
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="members"
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"