from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from tasks.permissions import TaskPermission
from tasks.serializers import TaskSerializer
from tasks.models import Task
from notifications.tasks import create_notification


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
        return Task.objects.filter(project__team=user.team)

    def perform_create(self, serializer):
        """Automatically assign the current user as creator and initial updater."""

        task = serializer.save(
            created_by=self.request.user, last_updated_by=self.request.user
        )

        if task.assigned_to:
            create_notification.delay(
                task.assigned_to.id,
                f"You were assigned task: {task.title}"
            )

    def perform_update(self, serializer):
        """Automatically update the last_updated_by field with the current user."""

        task = serializer.save(last_updated_by=self.request.user)

        if task.assigned_to:

            create_notification.delay(
                task.assigned_to.id,
                f"You were assigned task: {task.title}"
            )