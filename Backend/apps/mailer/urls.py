# from django.urls import path
# from rest_framework.routers import DefaultRouter
# from rest_framework.documentation import include_docs_urls
# from .views import SendEmailView, GenerateOTPView, VerifyOTPView, WelcomeEmailView, PasswordResetRequestView

# router = DefaultRouter()
# router.get_api_root_view().cls.__name__ = 'Mail API'
# router.get_api_root_view().cls.__doc__ = 'Available Mail API endpoints'

# urlpatterns = router.urls + [
#     path('send-email/', SendEmailView.as_view(), name='send-email'),
#     path('generate-otp/', GenerateOTPView.as_view(), name='generate-otp'),
#     path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
#     path('welcome-email/', WelcomeEmailView.as_view(), name='welcome-email'),
#     path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
# ]
