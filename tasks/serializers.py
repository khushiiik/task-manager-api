from rest_framework import serializers
from tasks.models import Task


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(
        source="assigned_to.username", read_only=True
    )

    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at"]
