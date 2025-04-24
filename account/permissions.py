from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsStartupOrPersonne(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'startupprofile') or hasattr(request.user, 'personneprofile')


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    - Anyone authenticated can view (SAFE_METHODS).
    - Only the owner (admin) can update/delete.
    """

    def has_object_permission(self, request, view, obj):
        # Safe methods: GET, HEAD, OPTIONS => allow for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Editing permissions: only the owner can modify
        # Adjust based on which model this is
        if hasattr(obj, 'personne'):
            return obj.personne == request.user
        if hasattr(obj, 'startup'):
            return obj.startup == request.user
        if hasattr(obj, 'bureau'):
            return obj.bureau == request.user

        return False