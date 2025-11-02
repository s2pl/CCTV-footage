from django.urls import path, include
from django.views.generic import TemplateView
from django.http import JsonResponse

app_name = 'cctv'

# Simple health check view
def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'CCTV System',
        'message': 'CCTV system is operational'
    })

urlpatterns = [
    # Web interface URLs (dashboard templates)
    path('', TemplateView.as_view(template_name='cctv/multi_stream_dashboard.html'), name='dashboard'),
    path('dashboard/', TemplateView.as_view(template_name='cctv/multi_stream_dashboard.html'), name='dashboard'),
    path('http-streaming/', TemplateView.as_view(template_name='cctv/http_stream_dashboard.html'), name='http_streaming'),
    
    # Health check for web views
    path('health/', health_check, name='health_check'),
    
    # Note: For camera views, recordings, schedules, and streams, use the REST API endpoints at /v0/api/cctv/
]
