from django.urls import path
from . import views

app_name = 'admin_custom'

urlpatterns = [
    path('admin/view/<int:id>/', views.admin_view_details, name='view_details'),
    path('admin/process/<int:id>/', views.admin_process_item, name='process_item'),
] 