from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, UserUpdateSerializer
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from accounts.models import User


class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class UserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer


class UserView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
