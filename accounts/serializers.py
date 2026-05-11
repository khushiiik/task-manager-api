from rest_framework import serializers
from accounts.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "email",
            "role",
            "team",
        ]

    def validate(self, attrs):

        role = attrs.get("role", User.Role.DEVELOPER)
        team = attrs.get("team")

        # Admin cannot belong to team.
        if role == User.Role.ADMIN and team:
            raise serializers.ValidationError("Admin cannot be assigned to a team.")

        # Only one manager and QA per team.
        if role in [User.Role.MANAGER, User.Role.QA] and team:

            queryset = User.objects.filter(role=role, team=team)

            # exclude self on update.
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)

            if queryset.exists():
                raise serializers.ValidationError(f"{role} already exists in the team.")

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance


class UserSerializer(serializers.ModelSerializer):

    team_name = serializers.CharField(source="team.name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "team_name"]
        read_only_fields = ["username", "role"]

class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):

        user = self.context["request"].user

        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError("Old password is incorrect.")

        return attrs

    def update(self, instance, validated_data):

        instance.set_password(validated_data["new_password"])

        instance.save()

        return instance