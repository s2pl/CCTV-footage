from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api import api as users_api

# Django REST Framework routes
router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'sessions', views.UserSessionViewSet, basename='sessions')
router.register(r'activities', views.UserActivityViewSet, basename='activities')

urlpatterns = [
    # Django REST Framework endpoints
    path('drf/', include(router.urls)),
    path('drf/create-user/', views.CreateUserView.as_view(), name='create-user'),
    
    # Django Ninja API endpoints (with Swagger docs)
    path('', users_api.urls),
]
