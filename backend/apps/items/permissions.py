from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsReporterOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.reporter_id == request.user.id or request.user.is_staff