from ninja import NinjaAPI, Schema, Router
from typing import List, Dict, Any, Optional
from .views import (
    EmailService,
    OTPService,
    WelcomeEmailService,
    PasswordResetService,
    CreatorBulkMailService,
    GeneralBulkMailService,
    CampaignService
)
from django.template.loader import render_to_string
from typing_extensions import Literal
# Import permission system and authentication
from apps.users.permissions import RoleBasedPermission, check_app_access, check_role_access
from apps.users.auth import verify_jwt_token

# Authentication class for Django Ninja
class JWTAuth:
    def authenticate(self, request, token):
        try:
            user = verify_jwt_token(token)
            # Check if user has access to mailer app
            if not check_app_access(user, 'mailer'):
                return None
            return user
        except Exception:
            return None

jwt_auth = JWTAuth()

api = NinjaAPI(urls_namespace='mailer_system')

# Create routers for mailer endpoints
authenticated_router = Router(tags=["Mailer System - Authenticated"])
public_router = Router(tags=["Mailer System - Public"])

class EmailSchema(Schema):
    subject: str
    message: str
    to_email: str

class OTPRequestSchema(Schema):
    to_email: str

class OTPVerifySchema(Schema):
    email: str
    otp: str

class WelcomeEmailSchema(Schema):
    email: str
    fullname: str

class UserCredentialsEmailSchema(Schema):
    user_id: str
    email: str
    username: str
    password: str
    role: str = "visitor"
    first_name: str = ""
    last_name: str = ""

class PasswordResetRequestSchema(Schema):
    email: str

class ResendOTPSchema(Schema):
    email: str

class RecipientSchema(Schema):
    email: str
    name: str

class CreatorBulkMailSchema(Schema):
    campaign_name: str
    subject: str
    message: str
    recipient_list: List[str]
    template_context: Optional[Dict[str, Any]] = {"recipients": []}
    template_name: Optional[str] = 'invitation/invite.html'
    from_email: Optional[str] = None

class GeneralBulkMailSchema(Schema):
    campaign_name: str
    subject: str
    message: str
    recipient_list: List[str]
    template_context: Optional[Dict[str, Any]] = {"recipients": []}
    cta_url: Optional[str] = None
    cta_text: Optional[str] = None
    from_email: Optional[str] = None

class TemplatePreviewSchema(Schema):
    template_name: str
    context: Dict[str, Any] = {}

# Public endpoints - no authentication required
@public_router.post("/request-password-reset", summary="Request Password Reset", description="Request password reset using OTP")
def request_password_reset(request, data: PasswordResetRequestSchema):
    """
    Request password reset using OTP verification - Public endpoint
    """
    return PasswordResetService.request_password_reset(data.email)

@public_router.post("/verify-otp", summary="Verify OTP", description="Verify OTP for email verification and password reset")
def verify_otp_public(request, data: OTPVerifySchema):
    """
    Verify OTP for password reset - Public endpoint
    """
    return OTPService.verify_otp(data.email, data.otp)

@public_router.post("/resend-otp", summary="Resend OTP", description="Resend OTP to user")
def resend_otp_public(request, data: ResendOTPSchema):
    """
    Resend OTP - Public endpoint
    """
    return OTPService.resend_otp(data.email)

# Authenticated endpoints - require authentication
@authenticated_router.post("/send-email", summary="Send Email", description="Send a single email")
def send_email(request, email_data: EmailSchema):
    # Check app access permission
    can_access, error_message = check_app_access(request.user, 'mailer', 'view_emails')
    if not can_access:
        return {"success": False, "error": error_message}
    
    return EmailService.send_email(email_data)

@authenticated_router.post("/generate-otp", summary="Generate OTP", description="Generate OTP for email verification")
def generate_otp(request, data: OTPRequestSchema):
    # Check app access permission
    can_access, error_message = check_app_access(request.user, 'mailer', 'view_emails')
    if not can_access:
        return {"success": False, "error": error_message}
    
    return OTPService.generate_otp(data.to_email)

@authenticated_router.post("/verify-otp-auth", summary="Verify OTP (Authenticated)", description="Verify OTP for authenticated operations")
def verify_otp(request, data: OTPVerifySchema):
    """
    Verify OTP for authenticated operations
    """
    # Check app access permission
    can_access, error_message = check_app_access(request.user, 'mailer', 'view_emails')
    if not can_access:
        return {"success": False, "error": error_message}
    
    return OTPService.verify_otp(data.email, data.otp)

@authenticated_router.post("/send-welcome-email", summary="Send Welcome Email", description="Send welcome email to new users")
def send_welcome_email(request, data: WelcomeEmailSchema):
    # Check app access permission
    can_access, error_message = check_app_access(request.user, 'mailer', 'send_emails')
    if not can_access:
        return {"success": False, "error": error_message}
    
    return WelcomeEmailService.send_welcome_email(data.email, data.fullname)

@authenticated_router.post("/send-user-credentials", summary="Send User Credentials Email", description="Send login credentials to new users")
def send_user_credentials_email(request, data: UserCredentialsEmailSchema):
    # Check app access permission - only admin and above can send credentials
    can_access, error_message = check_app_access(request.user, 'mailer', 'send_emails')
    if not can_access:
        return {"success": False, "error": error_message}
    
    # Additional permission check - only admin+ can send credentials
    if not (request.user.is_admin or request.user.is_superadmin):
        return {"success": False, "error": "Admin access required to send user credentials"}
    
    from .views import UserCredentialsEmailService
    
    user_data = {
        'id': data.user_id,
        'email': data.email,
        'username': data.username,
        'first_name': data.first_name,
        'last_name': data.last_name,
        'role': data.role
    }
    
    return UserCredentialsEmailService.send_user_credentials_email(
        user_data=user_data,
        created_by_user=request.user,
        plain_password=data.password
    )

# Advanced email functionality - accessible to managers and above
@authenticated_router.post("/send-bulk-email", summary="Send Bulk Email", description="Send bulk emails (managers and above)")
def send_bulk_email(request, data: List[EmailSchema]):
    return EmailService.send_bulk_email(data)

@authenticated_router.post("/send-email-attachment", summary="Send Email with Attachment", description="Send email with attachment (managers and above)")
def send_email_attachment(request, email_data: EmailSchema):
    return EmailService.send_email_with_attachment(email_data)

@authenticated_router.post("/send-bulk-creator-mail", summary="Send Bulk Creator Mail", description="Send bulk emails to creators (managers and above)")
def send_bulk_creator_mail(request, data: CreatorBulkMailSchema):
    """
    Send bulk emails to creators using the invitation template
    """
    return CreatorBulkMailService.send_bulk_mail(data)

@authenticated_router.post("/send-general-bulk-mail", summary="Send General Bulk Mail", description="Send general bulk emails (managers and above)")
def send_general_bulk_mail(request, data: GeneralBulkMailSchema):
    """
    Send general bulk emails using the general message template
    """
    return GeneralBulkMailService.send_general_bulk_mail(data)

# Campaign management - accessible to managers and above
@authenticated_router.get("/creator-mail-status/{campaign_id}", summary="Get Creator Mail Status", description="Get status of creator bulk email campaign")
def get_creator_mail_status(request, campaign_id: int):
    """
    Get status of a creator bulk email campaign
    """
    return CreatorBulkMailService.get_campaign_status(campaign_id)

@authenticated_router.get("/general-mail-status/{campaign_id}", summary="Get General Mail Status", description="Get status of general bulk email campaign")
def get_general_mail_status(request, campaign_id: int):
    """
    Get status of a general bulk email campaign
    """
    return GeneralBulkMailService.get_campaign_status(campaign_id)

@authenticated_router.get("/recent-campaigns", summary="Get Recent Campaigns", description="Get list of recent mail campaigns")
def get_recent_campaigns(request, limit: int = 5):
    """
    Get list of recent mail campaigns (both creator and general)
    """
    return CampaignService.get_recent_campaigns(limit)

@authenticated_router.get("/campaign-details/{campaign_id}", summary="Get Campaign Details", description="Get detailed campaign information")
def get_campaign_details(request, campaign_id: int):
    """
    Get detailed information about a specific campaign including recipient list
    """
    return CampaignService.get_campaign_details(campaign_id)

@authenticated_router.post("/preview-template", summary="Preview Template", description="Preview email template with context")
def preview_template(request, data: TemplatePreviewSchema):
    """
    Preview an email template with provided context
    """
    try:
        # Default empty context if none provided
        context = data.context or {}
        
        # Render the template with the provided context
        html_content = render_to_string(data.template_name, context)
        
        return {"status": "success", "html_content": html_content}
    except Exception as e:
        return {"status": "error", "message": f"Failed to render template: {str(e)}"}

# Add authentication to authenticated router
authenticated_router.auth = jwt_auth

# Include routers in main API
api.add_router("/", public_router)  # Public endpoints
api.add_router("/auth", authenticated_router)  # Authenticated endpoints

