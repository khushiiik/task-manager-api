from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from projects.serializers import ProjectSerializer
from projects.permissions import ProjectPermission
from projects.models import Project
from accounts.models import User


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectPermission]
    queryset = Project.objects.all()

    def get_queryset(self):
        user = self.request.user

        if user.role == user.Role.ADMIN:
            return Project.objects.all()

        return Project.objects.filter(team=user.team)

    def perform_create(self, serializer):
        """Automatically assign the current user as creator and initial updater."""

        project = serializer.save(
            created_by=self.request.user, last_updated_by=self.request.user
        )

        self.invalidate_project_cache(project)

    def perform_update(self, serializer):
        """Automatically update the last_updated_by field with the current user."""

        old_team_id = self.get_object().team_id

        project = serializer.save(last_updated_by=self.request.user)

        self.invalidate_project_cache(project, old_team_id)

    def perform_destroy(self, instance):
        self.invalidate_project_cache(instance)

        instance.delete()

    def bump_version(self, key):
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, None)

    def invalidate_project_cache(self, project, old_team_id=None):
        self.bump_version("admin_projects_version")

        self.bump_version(f"team_projects_{project.team_id}_version")

        if old_team_id and old_team_id != project.team_id:
            self.bump_version(f"team_projects_{old_team_id}_version")
