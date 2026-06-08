from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from teams.models import Team
from projects.models import Project
from tasks.models import Task
from chatbot.services.db_agent import assign_task_tool, create_task_tool

User = get_user_model()


class TaskPermissionsTestCase(APITestCase):

    def setUp(self):
        # Create team
        self.team = Team.objects.create(name="QA Dev Team")

        # Create users with different roles
        self.admin = User.objects.create_user(
            username="admin_user", password="password123", role="admin"
        )
        self.manager = User.objects.create_user(
            username="manager_user", password="password123", role="manager", team=self.team
        )
        self.developer = User.objects.create_user(
            username="developer_user", password="password123", role="developer", team=self.team
        )
        self.qa = User.objects.create_user(
            username="qa_user", password="password123", role="qa", team=self.team
        )
        self.other_user = User.objects.create_user(
            username="other_user", password="password123", role="developer", team=self.team
        )

        # Create project
        self.project = Project.objects.create(
            name="QA Dev Project", is_active=True, team=self.team
        )

        # Create task
        self.task = Task.objects.create(
            title="Initial Task",
            project=self.project,
            created_by=self.manager,
            last_updated_by=self.manager,
        )

        self.list_url = reverse("tasks-detail-list")
        self.detail_url = reverse("tasks-detail-detail", kwargs={"pk": self.task.id})

    def test_developer_can_create_task(self):
        self.client.force_authenticate(user=self.developer)
        data = {
            "title": "New Task from Dev",
            "project": self.project.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_qa_cannot_create_task(self):
        self.client.force_authenticate(user=self.qa)
        data = {
            "title": "New Task from QA",
            "project": self.project.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_qa_can_update_task_assignee(self):
        self.client.force_authenticate(user=self.qa)
        data = {
            "assigned_to": self.other_user.id,
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.other_user)

    def test_db_agent_assign_task_tool_permissions(self):
        # QA can assign task
        res_qa = assign_task_tool(
            task_id=self.task.id,
            username=self.other_user.username,
            user_id=self.qa.id,
        )
        self.assertTrue(res_qa.get("success"), res_qa.get("error"))

    def test_db_agent_create_task_tool_permissions(self):
        # Dev can create task
        res_dev = create_task_tool(
            title="Task from Tool",
            project_name=self.project.name,
            user_id=self.developer.id,
        )
        self.assertTrue(res_dev.get("success"), res_dev.get("error"))

        # QA cannot create task
        res_qa = create_task_tool(
            title="Task from Tool QA",
            project_name=self.project.name,
            user_id=self.qa.id,
        )
        self.assertIn("error", res_qa)
        self.assertIn("Permission Denied: QA cannot create tasks", res_qa["error"])
