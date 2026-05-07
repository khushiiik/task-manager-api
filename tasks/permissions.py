from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.models import User


class TaskPermission(BasePermission):

    def has_permission(self, request, view):

        # Read-only access for authenticated users.
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        
        # User must belong to a team.
        if not request.user.team and not request.user.role in [User.Role.ADMIN]:
            return False

        # DELETE permission.
        if request.method == "DELETE":
            return request.user.role in [
                User.Role.ADMIN,
                User.Role.MANAGER,
            ]

        # CREATE / UPDATE permission.
        return request.user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
            User.Role.DEVELOPER,
        ]
