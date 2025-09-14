from django.urls import path, include
from django.views.generic import TemplateView
from . import views

app_name = 'cctv'

urlpatterns = [
    # Admin URLs
    path('admin/', include('django.contrib.admin.urls')),
    
    # API URLs
    path('api/v0/', include('apps.cctv.api')),
    
    # Web interface URLs
    path('', TemplateView.as_view(template_name='cctv/multi_stream_dashboard.html'), name='dashboard'),
    path('dashboard/', TemplateView.as_view(template_name='cctv/multi_stream_dashboard.html'), name='dashboard'),
    path('http-streaming/', TemplateView.as_view(template_name='cctv/http_stream_dashboard.html'), name='http_streaming'),
    
    # Individual camera views
    path('camera/<uuid:camera_id>/', views.camera_detail, name='camera_detail'),
    path('camera/<uuid:camera_id>/stream/', views.camera_stream, name='camera_stream'),
    
    # Recording views
    path('recordings/', views.recording_list, name='recording_list'),
    path('recording/<uuid:recording_id>/', views.recording_detail, name='recording_detail'),
    
    # Schedule views
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedule/<uuid:schedule_id>/', views.schedule_detail, name='schedule_detail'),
    
    # Live stream views
    path('streams/', views.stream_list, name='stream_list'),
    path('stream/<uuid:stream_id>/', views.stream_detail, name='stream_detail'),
    
    # Test and diagnostic URLs
    path('test/', views.test_page, name='test_page'),
    path('health/', views.health_check, name='health_check'),
]
