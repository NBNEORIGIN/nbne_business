from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from .models import Config
from .config_loader import config as client_config


def health_check(request):
    """Health check endpoint"""
    import os
    from django.conf import settings as _settings
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Include client info in health check
    client_info = client_config.get_client_info()

    # AI assistant status
    key_from_settings = getattr(_settings, 'OPENAI_API_KEY', '')
    key_from_env = os.environ.get('OPENAI_API_KEY', '')
    ai_status = 'configured' if (key_from_settings or key_from_env) else 'not_configured'
    
    return JsonResponse({
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'database': db_status,
        'client': client_info.get('name', 'Unknown'),
        'mode': client_config.get_booking_mode(),
        'ai_assistant': ai_status,
        'ai_key_source': 'settings' if key_from_settings else ('environ' if key_from_env else 'none'),
        'ai_key_prefix': (key_from_settings or key_from_env)[:8] + '...' if (key_from_settings or key_from_env) else '',
    })


def home(request):
    """Homepage view"""
    # Get branding from client.config.json
    branding = client_config.get_branding()
    
    # Get features from client.config.json
    features = client_config.get_features()
    
    # Get client info
    client_info = client_config.get_client_info()
    
    # Override with database Config if exists
    for config_item in Config.objects.filter(category='branding'):
        key = config_item.key.replace('branding.', '')
        branding[key] = config_item.value
    
    for config_item in Config.objects.filter(category='features'):
        key = config_item.key.replace('features.', '')
        features[key] = config_item.value
    
    return render(request, 'core/home.html', {
        'branding': branding,
        'features': features,
        'client': client_info,
    })
