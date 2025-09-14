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
# from apps.users.api import api as users_api  # Old API - replaced with new user system
from apps.mailer.api import api as mailer_api
from apps.admin.api import api as admin_api
from apps.cctv.api import api as cctv_api
# from apps.cctv.api import api as cctv_api  # Temporarily disabled due to Django Ninja conflicts
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
urlpatterns = [
    # Health check endpoint for Docker
    path('health/', health_check, name='health_check'),
    
    path('admin/', admin.site.urls, name='django-admin'),
    path(f'{version}{sub}/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path(f'{version}{sub}/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # New User Management System
    path(f'{version}{sub}/users/', include('apps.users.urls')),
    
    # FastAPI-style endpoints  
    path(f'{version}{sub}/mail/', mailer_api.urls),
    path(f'{version}{sub}/admin/', admin_api.urls),
    path(f'{version}{sub}/cctv/', cctv_api.urls),  # Django Ninja API
   
]

# Add media and static URLs patterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
