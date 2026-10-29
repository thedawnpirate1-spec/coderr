from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Erlaubt Lesezugriff für alle Authentifizierten und Schreibzugriff nur für den Eigentümer."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

