from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read access to everyone, write access to admins only."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff