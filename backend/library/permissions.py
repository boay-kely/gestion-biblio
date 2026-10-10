from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStaffRole(BasePermission):
    """Admin ou bibliothécaire uniquement."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'is_staff_role', False))


class IsClientRole(BasePermission):
    """Client / lecteur authentifié."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'is_client_role', False))


class ReadOnlyOrStaff(BasePermission):
    """
    Lecture pour tout utilisateur authentifié.
    Création / modification / suppression réservées au staff.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(user, 'is_staff_role', False)


class IsStaffOrClientReadCreateOwn(BasePermission):
    """
    Staff : accès complet aux emprunts.
    Client : lecture + création (emprunt) uniquement.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_staff_role', False):
            return True
        if getattr(user, 'is_client_role', False):
            return request.method in SAFE_METHODS or request.method == 'POST'
        return False
