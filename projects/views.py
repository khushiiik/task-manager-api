from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from projects.serializers import ProjectSerializer
from projects.permissions import ProjectPermission
from projects.models import Project


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

        serializer.save(created_by=self.request.user, last_updated_by=self.request.user)

    def perform_update(self, serializer):
        """Automatically update the last_updated_by field with the current user."""

        serializer.save(last_updated_by=self.request.user)

    def list(self, request, *args, **kwargs):
        """Retrieve and cache project list separately for each user
        to improve performance while maintaining role-based access."""

        cache_key = f"project_{request.user.id}"

        cache_data = cache.get(cache_key)

        if cache_data:
            return Response(cache_data)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        cache.set(cache_key, serializer.data, timeout=60)

        return Response(serializer.data)
