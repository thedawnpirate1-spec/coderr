from rest_framework import permissions


class IsCustomerOrReadOnlyAuthenticated(permissions.BasePermission):
    """Erlaubt Lesezugriff für alle Eingeloggten und das Verfassen von Bewertungen nur für Kunden."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(request.user, 'profile') and request.user.profile.type == 'customer'


class IsReviewAuthorOrReadOnly(permissions.BasePermission):
    """Erlaubt das Bearbeiten oder Löschen einer Bewertung nur deren Verfasser."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.reviewer == request.user

