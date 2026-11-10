"""Custom permission classes for the orders API."""

from rest_framework import permissions


class IsCustomerForPostOrAuthenticated(permissions.BasePermission):
    """Allow any logged-in user to list orders, but only customers to create them."""

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


class IsOrderBusinessOrStaffDelete(permissions.BasePermission):
    """Allow status updates only for the ordered business user and deletion only for staff."""

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
        """Check whether the request may act on a specific order.

        Args:
            request: The incoming DRF request.
            view: The view handling the request.
            obj: The ``Order`` instance being accessed.

        Returns:
            For DELETE: True for staff only. For PATCH/PUT: True for the order's
            business user only. For reads: True for its customer, its business
            user and staff.
        """
        if request.method == 'DELETE':
            return bool(request.user.is_staff)
        if request.method in ('PATCH', 'PUT'):
            return obj.business_user == request.user
        return obj.customer_user == request.user or obj.business_user == request.user or request.user.is_staff
