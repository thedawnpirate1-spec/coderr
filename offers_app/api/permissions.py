"""Custom permission classes for the offers API."""

from rest_framework import permissions


class IsBusinessUserOrReadOnly(permissions.BasePermission):
    """Allow read access to everyone and write access only to business users."""

    def has_permission(self, request, view):
        """Check whether the request may reach the view.

        Args:
            request: The incoming DRF request.
            view: The view handling the request.

        Returns:
            True for safe methods, otherwise True only for authenticated users
            whose profile type is ``business``.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'profile') and request.user.profile.type == 'business'


class IsOfferOwnerOrReadOnly(permissions.BasePermission):
    """Allow modifying or deleting an offer only for the user who created it."""

    def has_object_permission(self, request, view, obj):
        """Check whether the request may act on a specific offer.

        Args:
            request: The incoming DRF request.
            view: The view handling the request.
            obj: The ``Offer`` instance being accessed.

        Returns:
            True for safe methods, otherwise True only for the offer's owner.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
