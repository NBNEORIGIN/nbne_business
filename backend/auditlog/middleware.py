from .models import AuditEntry


class AuditLogMiddleware:
    """Middleware that automatically logs authentication events and write operations."""

    # Paths to auto-log on successful POST/PATCH/DELETE
    WRITE_METHODS = {'POST', 'PATCH', 'PUT', 'DELETE'}

    # Skip these paths from auto-logging to avoid noise
    SKIP_PATHS = {'/api/auth/refresh/'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip non-API paths and excluded paths
        if not request.path.startswith('/api/'):
            return response
        if request.path in self.SKIP_PATHS:
            return response

        # Auto-log successful login
        if request.path == '/api/auth/login/' and request.method == 'POST':
            if 200 <= response.status_code < 300:
                AuditEntry.log(request, 'LOGIN', 'User', details='JWT login')
            return response

        # Auto-log write operations on success
        if request.method in self.WRITE_METHODS and 200 <= response.status_code < 300:
            action = self._infer_action(request)
            entity_type = self._infer_entity(request)
            if action and entity_type:
                AuditEntry.log(
                    request, action, entity_type,
                    details=f'{request.method} {request.path}',
                )

        return response

    @staticmethod
    def _infer_action(request):
        method = request.method
        path = request.path.rstrip('/')

        if method == 'DELETE':
            return 'DELETE'
        if method in ('PATCH', 'PUT'):
            if 'status' in path or 'role' in path:
                return 'STATUS_CHANGE'
            if 'password' in path:
                return 'PASSWORD_CHANGE'
            return 'UPDATE'
        if method == 'POST':
            if 'create' in path:
                return 'CREATE'
            if 'sign-off' in path or 'review' in path:
                return 'STATUS_CHANGE'
            if 'cancel' in path or 'confirm' in path:
                return 'STATUS_CHANGE'
            if 'export' in path:
                return 'EXPORT'
            return 'CREATE'
        return None

    @staticmethod
    def _infer_entity(request):
        path = request.path.rstrip('/')
        parts = [p for p in path.split('/') if p and p != 'api']

        # Walk path segments to find the entity type
        for segment in parts:
            if segment in (
                'bookings', 'services', 'staff', 'shifts', 'leave',
                'training', 'absence', 'channels', 'messages',
                'incidents', 'rams', 'documents', 'leads', 'users',
                'tenant', 'payments', 'recommendations',
                'categories', 'items', 'compliance', 'logs', 'calendar',
            ):
                return segment.title()
        return None
