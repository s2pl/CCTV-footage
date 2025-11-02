import csv
import json
from typing import List
from ninja import NinjaAPI, File, UploadedFile, Router
from ninja.files import UploadedFile
from django.http import HttpRequest
from django.db import transaction
from .models import Scraper

# Import permission system
from apps.users.permissions import RoleBasedPermission, check_app_access, check_role_access

# Create a Ninja API instance with CSRF disabled for testing
api = NinjaAPI(
    title="General System API",
    version="6.0.0",
    urls_namespace="general_system",
    csrf=False
)

# Create router for general endpoints
router = Router(tags=["General System"])

@router.post("/upload-csv", summary="Upload CSV Data", description="Upload CSV file with scraper data")
def upload_csv(request: HttpRequest, file: UploadedFile = File(...)):
    """
    Endpoint to upload a CSV file and store the data in the Scraper model.
    
    The CSV should have headers matching the model fields:
    - Username
    - Primary Contact
    - Email
    - Additional Emails
    - Phone
    - Additional Phones
    - Website
    - Bio
    - Followers
    - Following
    - Posts
    - Social Links
    - Contact Methods
    - Contact Aggregator
    """
    try:
        # Check user permissions
        if not request.user.is_authenticated:
            return {"success": False, "error": "Authentication required"}
        
        # Check app access permission
        can_access, error_message = check_app_access(request.user, 'general', 'manage_settings')
        if not can_access:
            return {"success": False, "error": error_message}
        
        # Only managers, admins, and superusers can upload CSV
        if not (request.user.is_staff or request.user.is_admin or request.user.is_superuser):
            return {"success": False, "error": "Permission denied. Only managers and above can upload CSV files."}
        
        # Decode the file content
        file_content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(file_content.splitlines())
        
        # Batch processing for better performance
        batch_size = 100
        scrapers_to_create = []
        
        with transaction.atomic():
            for row in csv_reader:
                # Process the data - convert to appropriate formats
                scraper_data = {
                    'username': row.get('Username', ''),
                    'primary_contact': row.get('Primary Contact', ''),
                    'email': row.get('Email', ''),
                    'additional_emails': parse_json_or_list(row.get('Additional Emails', '')),
                    'phone': row.get('Phone', ''),
                    'additional_phones': parse_json_or_list(row.get('Additional Phones', '')),
                    'website': row.get('Website', ''),
                    'bio': row.get('Bio', ''),
                    'followers': parse_int(row.get('Followers', 0)),
                    'following': parse_int(row.get('Following', 0)),
                    'posts': parse_int(row.get('Posts', 0)),
                    'social_links': parse_json_or_list(row.get('Social Links', '')),
                    'contact_methods': parse_json_or_list(row.get('Contact Methods', '')),
                    'contact_aggregator': parse_json_or_list(row.get('Contact Aggregator', '')),
                    'created_by': request.user,  # Track who uploaded the data
                }
                
                scrapers_to_create.append(Scraper(**scraper_data))
                
                # Insert in batches for better performance
                if len(scrapers_to_create) >= batch_size:
                    Scraper.objects.bulk_create(scrapers_to_create)
                    scrapers_to_create = []
            
            # Insert any remaining records
            if scrapers_to_create:
                Scraper.objects.bulk_create(scrapers_to_create)
        
        return {"success": True, "message": "CSV data imported successfully"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/dashboard", summary="General Dashboard", description="Get general system dashboard data")
def get_dashboard(request: HttpRequest):
    """Get general dashboard data accessible to all authenticated users"""
    if not request.user.is_authenticated:
        return {"success": False, "error": "Authentication required"}
    
    # Check app access permission
    can_access, error_message = check_app_access(request.user, 'general', 'view_dashboard')
    if not can_access:
        return {"success": False, "error": error_message}
    
    # Basic dashboard data for all users
    dashboard_data = {
        "user_role": RoleBasedPermission.get_user_role(request.user),
        "total_scrapers": Scraper.objects.count(),
        "system_status": "operational"
    }
    
    # Additional data for managers and above
    if request.user.is_staff or request.user.is_admin or request.user.is_superuser:
        dashboard_data.update({
            "recent_uploads": Scraper.objects.order_by('-created_at')[:5].count(),
            "system_metrics": {
                "total_users": "N/A",  # Will be populated from users app
                "total_cameras": "N/A",  # Will be populated from CCTV app
                "total_emails": "N/A"   # Will be populated from mailer app
            }
        })
    
    return {"success": True, "data": dashboard_data}

@router.get("/settings", summary="System Settings", description="Get system settings (managers and above)")
def get_settings(request: HttpRequest):
    """Get system settings - only accessible to managers and above"""
    if not request.user.is_authenticated:
        return {"success": False, "error": "Authentication required"}
    
    # Check app access permission
    can_access, error_message = check_app_access(request.user, 'general', 'manage_settings')
    if not can_access:
        return {"success": False, "error": error_message}
    
    # Only managers, admins, and superusers can access settings
    if not (request.user.is_staff or request.user.is_admin or request.user.is_superuser):
        return {"success": False, "error": "Permission denied. Only managers and above can access settings."}
    
    settings_data = {
        "system_name": "Shree Swami Smartha System",
        "version": "1.0.0",
        "maintenance_mode": False,
        "user_management": {
            "allow_registration": True,
            "require_email_verification": True
        }
    }
    
    return {"success": True, "data": settings_data}

# Include router in main API
api.add_router("/", router)

def parse_int(value):
    """Convert a value to integer, return None if conversion fails."""
    if not value:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def parse_json_or_list(value):
    """Convert a value to JSON if it's a string, or return an empty dict."""
    if not value:
        return {}
    
    # If it's already a dict or list, return it
    if isinstance(value, (dict, list)):
        return value
    
    # Try parsing as JSON
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        # If it's not valid JSON, check if it's a comma-separated list
        if isinstance(value, str) and ',' in value:
            return value.split(',')
        return value 