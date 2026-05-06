from rest_framework import serializers
from accounts.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "email", "role", "team"]

    def validate(self, attrs):
        role = attrs.get("role", User.Role.DEVELOPER)
        team = attrs.get("team")

        if role == User.Role.ADMIN:
            raise serializers.ValidationError("Cannot register as admin.")

        if role in [User.Role.MANAGER, User.Role.QA] and team:
            exist = User.objects.filter(team=team, role=role).exists()

            if exist:
                raise serializers.ValidationError(f"{role} already exists in the team.")

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email"),
            role=validated_data.get("role", User.Role.DEVELOPER),
            team=validated_data.get("team"),
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["role", "team"]

    def validate(self, attrs):
        role = attrs.get("role", self.instance.role)
        team = attrs.get("team", self.instance.team)

        if role in [User.Role.MANAGER, User.Role.QA] and team:
            exists = (
                User.objects.filter(team=team, role=role)
                .exclude(id=self.instance.id)
                .exists()
            )
            if exists:
                raise serializers.ValidationError(
                    f"{role} already exists in this team."
                )

        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "team"]
