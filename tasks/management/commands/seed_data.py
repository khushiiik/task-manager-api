import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from teams.models import Team
from projects.models import Project
from tasks.models import Task


class Command(BaseCommand):
    help = "Seeds the database with test data (Teams, Users, Projects, and Tasks) excluding chatbot."

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing existing data (excluding chatbot)...")
        # Clear existing non-chatbot data
        Task.objects.all().delete()
        Project.objects.all().delete()
        User.objects.all().delete()
        Team.objects.all().delete()

        self.stdout.write("Seeding database...")

        # 1. Create Teams
        team_a = Team.objects.create(name="Team Alpha")
        team_b = Team.objects.create(name="Team Beta")
        self.stdout.write(f"Created teams: {team_a.name}, {team_b.name}")

        # 2. Create 11 Users
        # 1 Admin
        admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123",
            role=User.Role.ADMIN,
        )

        # 2 Managers
        manager_a = User.objects.create_user(
            username="manager_alpha",
            email="manager_a@example.com",
            password="password123",
            role=User.Role.MANAGER,
            team=team_a,
        )
        manager_b = User.objects.create_user(
            username="manager_beta",
            email="manager_b@example.com",
            password="password123",
            role=User.Role.MANAGER,
            team=team_b,
        )

        # 2 QAs
        qa_a = User.objects.create_user(
            username="qa_alpha",
            email="qa_a@example.com",
            password="password123",
            role=User.Role.QA,
            team=team_a,
        )
        qa_b = User.objects.create_user(
            username="qa_beta",
            email="qa_b@example.com",
            password="password123",
            role=User.Role.QA,
            team=team_b,
        )

        # 6 Developers (3 in Team A, 3 in Team B)
        devs_a = []
        for i in range(1, 4):
            dev = User.objects.create_user(
                username=f"dev_alpha_{i}",
                email=f"dev_a_{i}@example.com",
                password="password123",
                role=User.Role.DEVELOPER,
                team=team_a,
            )
            devs_a.append(dev)

        devs_b = []
        for i in range(1, 4):
            dev = User.objects.create_user(
                username=f"dev_beta_{i}",
                email=f"dev_b_{i}@example.com",
                password="password123",
                role=User.Role.DEVELOPER,
                team=team_b,
            )
            devs_b.append(dev)

        self.stdout.write("Created 11 users (1 Admin, 2 Managers, 2 QAs, 6 Developers).")

        # 3. Create 3 Projects per team
        projects_a = []
        for i in range(1, 4):
            proj = Project.objects.create(
                name=f"Project Alpha {i}",
                is_active=True,
                team=team_a,
                created_by=manager_a,
                last_updated_by=manager_a,
                start_date=timezone.now().date(),
                end_date=(timezone.now() + timezone.timedelta(days=30)).date(),
            )
            projects_a.append(proj)

        projects_b = []
        for i in range(1, 4):
            proj = Project.objects.create(
                name=f"Project Beta {i}",
                is_active=True,
                team=team_b,
                created_by=manager_b,
                last_updated_by=manager_b,
                start_date=timezone.now().date(),
                end_date=(timezone.now() + timezone.timedelta(days=30)).date(),
            )
            projects_b.append(proj)

        self.stdout.write("Created 6 projects (3 for Team Alpha, 3 for Team Beta).")

        # 4. Create 3 Tasks per Project
        all_projects = projects_a + projects_b
        states = [Task.State.DRAFT, Task.State.IN_PROGRESS, Task.State.COMPLETED, Task.State.BLOCKED]

        for project in all_projects:
            # Determine developers available for assignment based on project's team
            available_devs = devs_a if project.team == team_a else devs_b
            creator = manager_a if project.team == team_a else manager_b

            for task_idx in range(1, 4):
                # We need some task assignees to be empty. Let's make the 3rd task of each project unassigned.
                if task_idx == 3:
                    assignee = None
                else:
                    assignee = random.choice(available_devs)

                Task.objects.create(
                    title=f"Task {task_idx} for {project.name}",
                    description=f"This is the description for Task {task_idx} of {project.name}.",
                    state=random.choice(states),
                    priority=random.choice([True, False]),
                    project=project,
                    assigned_to=assignee,
                    created_by=creator,
                    last_updated_by=creator,
                    deadline=timezone.now() + timezone.timedelta(days=random.randint(5, 15)),
                )

        self.stdout.write("Created 3 tasks per project (with some tasks unassigned).")
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
