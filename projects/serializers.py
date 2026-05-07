from rest_framework import serializers
from projects.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )

    last_updated_by_name = serializers.CharField(
        source="last_updated_by.username", read_only=True
    )

    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at", "last_updated_by"]
