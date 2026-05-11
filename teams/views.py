from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from teams.serializers import TeamSerializer
from accounts.serializers import UserSerializer
from teams.permissions import TeamPermission
from teams.models import Team


class TeamViewSet(ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, TeamPermission]
    queryset = Team.objects.all()

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        team = self.get_object()
        serializer = UserSerializer(team.members.all(), many=True)
        return Response(serializer.data)
