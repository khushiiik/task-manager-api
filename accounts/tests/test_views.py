from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class ProfileViewTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", password="test12345", email="test@gmail.com"
        )

        self.url = reverse("profile")
    
    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "test_user")
    
    def test_get_profile_unauthenticated(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)