from django.test import TestCase
from projects.models import Project
from teams.models import Team


class UserCreateTestCase(TestCase):
    def setUp(self):
        self.team = Team.objects.create(name="Test Team")
        self.project = Project.objects.create(
            name="Test Project", is_active=True, team=self.team
        )

    def test_project_created(self):
        self.assertEqual(self.project.name, "Test Project")
        self.assertTrue(self.project.is_active)
        self.assertEqual(self.project.team.name, "Test Team")
