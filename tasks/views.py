from django.db import connection
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from tasks.filters import TaskFilter
from tasks.permissions import TaskPermission, TaskReportPermission
from tasks.serializers import TaskSerializer
from tasks.models import Task
from notifications.tasks import create_notification


class TasksViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, TaskPermission]
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
            Q(project__team=user.team) | Q(assigned_to=user), project__is_active=True
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
        old_assigned_to = self.get_object().assigned_to

        task = serializer.save(last_updated_by=self.request.user)

        # Notify only if assignee changed.
        if old_assigned_to != task.assigned_to:

            if task.assigned_to:

                create_notification.delay(
                    task.assigned_to.id, f"You were assigned task: {task.title}"
                )


class OverdueTaskReportView(APIView):

    permission_classes = [IsAuthenticated, TaskReportPermission]

    def get(self, request):
        """This view returns a list of users along with the total number
        of overdue tasks assigned to them."""

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    accounts_user.username,
                    COUNT(tasks_task.id) AS total_overdue_tasks
                FROM tasks_task
                JOIN accounts_user
                    ON tasks_task.assigned_to_id = accounts_user.id
                WHERE
                    tasks_task.deadline < NOW()
                    AND tasks_task.state != 'completed'
                    AND projects_project.is_active = TRUE
                GROUP BY accounts_user.username
                ORDER BY total_overdue_tasks DESC;
            """)

            rows = cursor.fetchall()

        data = [{"username": row[0], "total_overdue_tasks": row[1]} for row in rows]

        return Response(data)
