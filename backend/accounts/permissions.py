from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Only owners can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'owner'


class IsManagerOrAbove(BasePermission):
    """Managers and owners can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager_or_above


class IsStaffOrAbove(BasePermission):
    """Staff, managers, and owners can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff_or_above


class IsCustomerOrAbove(BasePermission):
    """Any authenticated user can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsSelfOrManagerAbove(BasePermission):
    """User can access their own data, or managers/owners can access anyone's."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_manager_or_above:
            return True
        return obj == request.user or getattr(obj, 'user', None) == request.user


def role_required(*roles):
    """Decorator-style permission factory for function-based views.

    Usage:
        @api_view(['GET'])
        @permission_classes([role_required('manager', 'owner')])
        def my_view(request): ...
    """
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            return request.user.is_authenticated and request.user.role in roles
    RolePermission.__name__ = f"RoleRequired_{'_'.join(roles)}"
    return RolePermission
