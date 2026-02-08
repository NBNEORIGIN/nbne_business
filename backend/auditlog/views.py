from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from accounts.permissions import IsManagerOrAbove
from .models import AuditEntry
from .serializers import AuditEntrySerializer


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def audit_list(request):
    """List audit entries (managers/owners only).

    Query params:
        action   — filter by action type
        user_id  — filter by user
        entity   — filter by entity_type
        limit    — max results (default 100)
    """
    entries = AuditEntry.objects.all()

    action = request.query_params.get('action')
    if action:
        entries = entries.filter(action=action)

    user_id = request.query_params.get('user_id')
    if user_id:
        entries = entries.filter(user_id=user_id)

    entity = request.query_params.get('entity')
    if entity:
        entries = entries.filter(entity_type__icontains=entity)

    limit = int(request.query_params.get('limit', 100))
    entries = entries[:limit]

    serializer = AuditEntrySerializer(entries, many=True)
    return Response(serializer.data)
