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

    # Auto assign creator.
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
