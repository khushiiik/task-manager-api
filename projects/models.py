from django.db import models
from accounts.models import User
from teams.models import Team


class Project(models.Model):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_projects"
    )
    last_updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="updated_projects"
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
