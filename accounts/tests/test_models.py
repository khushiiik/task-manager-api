from django.test import TestCase
from accounts.models import User

class UserCreateTestCase(TestCase):
    def setUp(self):
        self.instance = User.objects.create_user(username="test_name", password="test_123", email="test@gmail.com")
    
    def test_instance_username(self):
        self.assertEqual(self.instance.username, "test_name")
        self.assertTrue(self.instance.check_password("test_123"))