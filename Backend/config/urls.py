from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
# Dashboard removed for boilerplate

def health_check(request):
    """Health check endpoint for Docker"""
    try:
        # Check database connection
        db_conn = connections['default']
        db_conn.cursor()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
    except OperationalError:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }, status=503)

version = 'v0'
# sub = '/ninja'
sub = '/api'

# Use late binding to avoid namespace conflicts during import
# Import APIs only when needed (inside a function that returns the urls)
urlpatterns = [
    # Health check endpoint for Docker
    path('health/', health_check, name='health_check'),
    
    path('admin/', admin.site.urls, name='django-admin'),
    path(f'{version}{sub}/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path(f'{version}{sub}/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # New User Management System
    path(f'{version}{sub}/users/', include('apps.users.urls')),
    
    # CCTV Web Views (traditional Django views for templates)
    path('cctv/', include('apps.cctv.urls')),  # /cctv/* for web interfaces
   
]

# Lazy import APIs after initial urlpatterns to avoid circular imports
def _setup_api_urls():
    """Set up API URLs with late binding to avoid namespace conflicts"""
    from apps.mailer.api import api as mailer_api
    from apps.admin.api import api as admin_api
    from apps.cctv.api import api as cctv_api, local_client_api
    
    urlpatterns.extend([
        # FastAPI-style endpoints  
        path(f'{version}{sub}/mail/', mailer_api.urls),
        path(f'{version}{sub}/admin/', admin_api.urls),
        path(f'{version}{sub}/cctv/', cctv_api.urls),  # Django Ninja API
        
        # Direct local-client API routes (for compatibility)
        path(f'{version}{sub}/local-client/', local_client_api.urls),  # /api/local-client/*
    ])

# Call the setup function to add API URLs
_setup_api_urls()

# Add media and static URLs patterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
