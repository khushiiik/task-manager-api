from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from tasks.permissions import TaskPermission
from tasks.serializers import TaskSerializer
from tasks.models import Task


class TasksViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, TaskPermission]
    queryset = Task.objects.all()

    def get_queryset(self):
        user = self.request.user

        # Visible all teams tasks.
        if user.role == user.Role.ADMIN:
            return Task.objects.all()

        # Visible only team tasks.
        if user.role == user.Role.MANAGER:
            return Task.objects.filter(project__team=user.team)

        # Visible only assigned tasks.
        return Task.objects.filter(assigned_to=user)
