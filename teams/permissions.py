from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.models import User


class TeamPermission(BasePermission):

    def has_permission(self, request, view):

        # Read-only access for authenticated users.
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        # Only admin & manager can modify.
        return request.user.role in [
            User.Role.ADMIN,
        ]
