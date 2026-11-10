"""Custom permission classes for the reviews API."""

from rest_framework import permissions


class IsCustomerOrReadOnlyAuthenticated(permissions.BasePermission):
    """Allow any logged-in user to read reviews, but only customers to write them."""

    def has_permission(self, request, view):
        """Check whether the request may reach the view.

        Args:
            request: The incoming DRF request.
            view: The view handling the request.

        Returns:
            True for authenticated users on safe methods, and for authenticated
            users with a ``customer`` profile on all other methods.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(request.user, 'profile') and request.user.profile.type == 'customer'


class IsReviewAuthorOrReadOnly(permissions.BasePermission):
    """Allow editing or deleting a review only for its author."""

    def has_permission(self, request, view):
        """Require an authenticated user.

        Args:
            request: The incoming DRF request.
            view: The view handling the request.

        Returns:
            True if the user is authenticated.
        """
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Check whether the request may act on a specific review.

        Args:
            request: The incoming DRF request.
            view: The view handling the request.
            obj: The ``Review`` instance being accessed.

        Returns:
            True for safe methods, otherwise True only for the review's author.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.reviewer == request.user
