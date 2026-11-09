from rest_framework import permissions


class IsCustomerForPostOrAuthenticated(permissions.BasePermission):
    """Erlaubt das Auflisten für alle Eingeloggten und das Bestellen nur für Kunden-Profile."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(request.user, 'profile') and request.user.profile.type == 'customer'


class IsOrderBusinessOrStaffDelete(permissions.BasePermission):
    """Erlaubt Status-Updates nur dem beauftragten Anbieter und das Löschen nur Staff-Nutzern."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return bool(request.user.is_staff)
        if request.method in ('PATCH', 'PUT'):
            return obj.business_user == request.user
        return obj.customer_user == request.user or obj.business_user == request.user or request.user.is_staff

