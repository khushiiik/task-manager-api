from rest_framework.viewsets import ModelViewSet
from teams.serializers import TeamSerializer
from teams.models import Team
from rest_framework.decorators import action
from accounts.serializers import UserSerializer
from rest_framework.response import Response


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        team = self.get_object()
        serializer = UserSerializer(team.members.all(), many=True)
        return Response(serializer.data)
