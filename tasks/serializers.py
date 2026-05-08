from rest_framework import serializers
from tasks.models import Task
from accounts.models import User
from projects.models import Project


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(
        source="assigned_to.username", read_only=True
    )

    project_name = serializers.CharField(source="project.name", read_only=True)

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )

    last_updated_by_name = serializers.CharField(
        source="last_updated_by.username", read_only=True
    )

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at", "last_updated_by"]

    def __init__(self, *args, **kwargs):
        """Filter users and projects by request user's team.Excludes admin users from task assignment options."""

        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and request.user.team:
            self.fields["assigned_to"].queryset = User.objects.filter(
                team=request.user.team
            ).exclude(role=User.Role.ADMIN)

            self.fields["project"].queryset = Project.objects.filter(
                team=request.user.team
            )

    def validate(self, attrs):

        request = self.context["request"]

        project = attrs.get("project")
        assigned_to = attrs.get("assigned_to")

        if project and assigned_to:

            # Prevent assigning tasks to admin users.
            if assigned_to.role == User.Role.ADMIN:
                raise serializers.ValidationError(
                    "Admin cannot be assigned to any task."
                )

            # Ensure selected user belongs to a team.
            if not assigned_to.team:
                raise serializers.ValidationError(
                    "Cannot assign task because the selected user is not assigned to any team."
                )

            # Non-admin users can assign tasks only within the same project team.
            if request.user.role != User.Role.ADMIN:

                if project.team != assigned_to.team:
                    raise serializers.ValidationError(
                        "Assigned user must belong to the project team."
                    )

        return attrs
