from rest_framework import permissions


class IsBusinessUserOrReadOnly(permissions.BasePermission):
    """Erlaubt Lesezugriff für alle und das Erstellen von Angeboten nur für Business-Nutzer."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'profile') and request.user.profile.type == 'business'


class IsOfferOwnerOrReadOnly(permissions.BasePermission):
    """Erlaubt Änderungen oder das Löschen eines Angebots nur dem jeweiligen Ersteller."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

