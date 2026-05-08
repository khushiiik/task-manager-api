from django.db.models import Q
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from tasks.filters import TaskFilter
from tasks.permissions import TaskPermission
from tasks.serializers import TaskSerializer
from tasks.models import Task
from notifications.tasks import create_notification


class TasksViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, TaskPermission]
    queryset = Task.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    def get_queryset(self):
        user = self.request.user

        # Visible all teams tasks.
        if user.role == user.Role.ADMIN:
            return Task.objects.all()

        # Manager can view all team tasks, including inactive project tasks.
        if user.role == user.Role.MANAGER:
            return Task.objects.filter(
                Q(project__team=user.team) | Q(assigned_to=user)
            ).distinct()

        # Team members can only view tasks from active projects.
        return Task.objects.filter(
            Q(project__team=user.team) | Q(assigned_to=user),
            project__is_active=True
        ).distinct()

    def perform_create(self, serializer):
        """Automatically assign the current user as creator and initial updater."""

        task = serializer.save(
            created_by=self.request.user, last_updated_by=self.request.user
        )

        if task.assigned_to:
            create_notification.delay(
                task.assigned_to.id, f"You were assigned task: {task.title}"
            )

    def perform_update(self, serializer):
        """Automatically update the last_updated_by field with the current user."""

        task = serializer.save(last_updated_by=self.request.user)

        if task.assigned_to:

            create_notification.delay(
                task.assigned_to.id, f"You were assigned task: {task.title}"
            )
