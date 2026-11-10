"""Custom permission classes for the profiles API."""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow read access to authenticated users and write access only to the profile owner."""

    def has_object_permission(self, request, view, obj):
        """Check whether the request may act on a specific profile.

        Args:
            request: The incoming DRF request.
            view: The view handling the request.
            obj: The ``UserProfile`` instance being accessed.

        Returns:
            True for safe methods, otherwise True only for the profile's owner.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
