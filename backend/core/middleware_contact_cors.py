"""
Tiny middleware that handles CORS for the public /api/contact/ endpoint.

Placed BEFORE django-cors-headers in the middleware stack so it intercepts
the OPTIONS preflight before corsheaders can return a response without
the Access-Control-Allow-Origin header (which happens when Railway's
CORS_ALLOWED_ORIGINS env var doesn't include business.nbne.uk).
"""

ALLOWED_ORIGINS = {
    'https://business.nbne.uk',
    'https://nbne-landing.vercel.app',
    'http://localhost:3000',
}


class ContactCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only intercept /api/contact/
        if request.path.rstrip('/') != '/api/contact':
            return self.get_response(request)

        origin = request.META.get('HTTP_ORIGIN', '')

        # Handle preflight
        if request.method == 'OPTIONS' and origin in ALLOWED_ORIGINS:
            from django.http import HttpResponse
            resp = HttpResponse(status=200)
            resp['Access-Control-Allow-Origin'] = origin
            resp['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            resp['Access-Control-Allow-Headers'] = 'Content-Type'
            resp['Access-Control-Max-Age'] = '86400'
            return resp

        # Normal request — let the view handle it, then add CORS headers
        response = self.get_response(request)
        if origin in ALLOWED_ORIGINS:
            response['Access-Control-Allow-Origin'] = origin
        return response
