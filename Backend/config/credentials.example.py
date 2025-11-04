"""
Credentials Configuration Template
===================================
Copy this file to 'credentials.py' and fill in your actual credentials.
DO NOT commit credentials.py to version control!

For production, use environment variables instead of hardcoded values.
"""

import os

# ================================
# Django Secret Key
# ================================
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# ================================
# Database Credentials
# ================================
DATABASE = {
    'NAME': os.getenv('DB_NAME', 'your_database_name'),
    'USER': os.getenv('DB_USER', 'your_database_user'),
    'PASSWORD': os.getenv('DB_PASSWORD', 'your_database_password'),
    'HOST': os.getenv('DB_HOST', 'your_database_host'),
    'PORT': os.getenv('DB_PORT', '5432'),
}

# ================================
# Email Credentials
# ================================
EMAIL = {
    'HOST': 'smtp.gmail.com',
    'PORT': 587,
    'USE_TLS': True,
    'USE_SSL': False,
    'HOST_USER': 'your_email@gmail.com',
    'HOST_PASSWORD': 'your_app_password',
    'DEFAULT_FROM': 'your_email@gmail.com',
}

# ================================
# AWS S3 Credentials
# ================================
AWS = {
    'ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID', 'your_aws_access_key'),
    'SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY', 'your_aws_secret_key'),
    'SESSION_TOKEN': os.getenv('AWS_SESSION_TOKEN', ''),
    'REGION_NAME': os.getenv('AWS_REGION_NAME', 'ap-south-1'),
    'STORAGE_BUCKET_NAME': os.getenv('AWS_STORAGE_BUCKET_NAME', 'your-bucket-name'),
}

# ================================
# GCP Cloud Storage Credentials
# ================================
GCP = {
    'STORAGE_BUCKET_NAME': os.getenv('GCP_STORAGE_BUCKET_NAME', 'your_gcp_bucket'),
    'STORAGE_PROJECT_ID': os.getenv('GCP_STORAGE_PROJECT_ID', 'your-project-id'),
    'STORAGE_CREDENTIALS_PATH': os.getenv('GCP_STORAGE_CREDENTIALS_PATH', 'credentials/your-credentials.json'),
    'STORAGE_USE_GCS': os.getenv('GCP_STORAGE_USE_GCS', 'False').lower() == 'true',
}

# ================================
# JWT Token Settings
# ================================
JWT = {
    'ALGORITHM': os.getenv('JWT_ALGORITHM', 'HS256'),
    'SECRET_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),
}

# ================================
# Admin Settings
# ================================
ADMIN = {
    'URL': os.getenv('ADMIN_URL', 'admin/'),
    'EMAIL': 'admin@example.com',
    'NAME': 'Admin Name',
}

