from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from accounts.permissions import IsOwner
from .models import TenantSettings
from .serializers import TenantSettingsSerializer, TenantSettingsCSSVarsSerializer, TenantSettingsUpdateSerializer


def _get_tenant(request):
    """Resolve tenant from ?tenant=slug query param, or return first."""
    slug = request.query_params.get('tenant')
    return TenantSettings.load(slug=slug)


@api_view(['GET'])
@permission_classes([AllowAny])
def tenant_settings(request):
    """Return full tenant settings (public, read-only)."""
    obj = _get_tenant(request)
    if not obj:
        return Response({'detail': 'Tenant not found'}, status=404)
    serializer = TenantSettingsSerializer(obj)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def tenant_branding(request):
    """Return minimal branding/CSS-variable data for the frontend."""
    obj = _get_tenant(request)
    if not obj:
        return Response({'detail': 'Tenant not found'}, status=404)
    serializer = TenantSettingsCSSVarsSerializer(obj)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsOwner])
def tenant_update(request):
    """Update tenant settings (owner only)."""
    obj = _get_tenant(request)
    if not obj:
        return Response({'detail': 'Tenant not found'}, status=404)
    serializer = TenantSettingsUpdateSerializer(obj, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    serializer.save()
    return Response(TenantSettingsSerializer(obj).data)
