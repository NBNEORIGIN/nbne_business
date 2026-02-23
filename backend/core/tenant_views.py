"""
Tenant views that bridge the Config model to the NBNE-style frontend expectations.
The frontend calls /api/tenant/branding/ and /api/tenant/ expecting specific field names.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Config
from .config_loader import config as client_config


@api_view(['GET'])
@permission_classes([AllowAny])
def tenant_branding_view(request):
    """
    Returns branding config in the format the NBNE frontend expects:
    { slug, business_name, enabled_modules, colour_primary, colour_secondary, ... }
    """
    # Start with defaults from client.config.json
    branding = client_config.get_branding()
    client_info = client_config.get_client_info()
    features = client_config.get_features()

    # Override with DB Config entries
    for item in Config.objects.filter(category='branding'):
        key = item.key.replace('branding.', '')
        branding[key] = item.value

    # Build enabled_modules list from features
    enabled_modules = []
    module_map = {
        'bookings': True,
        'staff': True,
        'compliance': True,
        'documents': True,
        'comms': True,
        'crm': True,
    }
    for mod, default in module_map.items():
        feat_key = f'features.{mod}'
        feat_val = features.get(mod, str(default)).lower()
        if feat_val in ('true', '1', 'yes'):
            enabled_modules.append(mod)

    return Response({
        'slug': branding.get('slug', client_info.get('slug', 'default')),
        'business_name': branding.get('business_name', client_info.get('name', 'NBNE Business')),
        'enabled_modules': enabled_modules,
        'tagline': branding.get('tagline', ''),
        'colour_primary': branding.get('colour_primary', branding.get('primary_color', '#2563eb')),
        'colour_secondary': branding.get('colour_secondary', branding.get('secondary_color', '#1e40af')),
        'colour_background': branding.get('colour_background', '#ffffff'),
        'colour_text': branding.get('colour_text', '#333333'),
        'currency_symbol': branding.get('currency_symbol', '£'),
        'logo_url': branding.get('logo_url', ''),
        'favicon_url': branding.get('favicon_url', ''),
        'font_heading': branding.get('font_heading', ''),
        'font_body': branding.get('font_body', ''),
        'font_url': branding.get('font_url', ''),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def tenant_settings_view(request):
    """
    Returns tenant settings in the format the NBNE frontend expects.
    """
    branding = client_config.get_branding()
    client_info = client_config.get_client_info()

    for item in Config.objects.filter(category='branding'):
        key = item.key.replace('branding.', '')
        branding[key] = item.value

    return Response({
        'business_name': branding.get('business_name', client_info.get('name', 'NBNE Business')),
        'email': branding.get('email', ''),
        'phone': branding.get('phone', ''),
        'address': branding.get('address', ''),
        'colour_primary': branding.get('colour_primary', branding.get('primary_color', '#2563eb')),
        'colour_secondary': branding.get('colour_secondary', branding.get('secondary_color', '#1e40af')),
        'deposit_percentage': 0,
    })
