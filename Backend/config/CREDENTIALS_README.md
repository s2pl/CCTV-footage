# Credentials Configuration Guide

## Overview

This folder contains a separate `credentials.py` file for managing all sensitive credentials and API keys. This approach keeps your sensitive data separate from your main settings file and makes it easier to manage security.

## Files

### 1. `credentials.py` (DO NOT COMMIT!)
This is your **actual credentials file** containing real sensitive data. This file should:
- ✅ Be in `.gitignore` (already configured)
- ✅ Never be committed to version control
- ✅ Be kept secure on your local machine or secure deployment environment

### 2. `credentials.example.py` (Safe to commit)
This is a **template file** showing what credentials need to be configured. Team members can:
- Copy this file to `credentials.py`
- Fill in their own credentials
- Start development immediately

### 3. `settings.py`
The main Django settings file now imports credentials from `credentials.py` instead of having them hardcoded.

## Setup Instructions

### For New Developers

1. **Copy the example file:**
   ```bash
   cd Backend/config
   cp credentials.example.py credentials.py
   ```

2. **Edit `credentials.py` and fill in your actual credentials:**
   - Database credentials
   - AWS S3 credentials
   - Email credentials
   - GCP credentials (if using)
   - JWT secret key

3. **Verify the file is ignored:**
   ```bash
   git status
   # credentials.py should NOT appear in the list
   ```

### For Production Deployment

**Best Practice:** Use environment variables instead of hardcoded values!

1. **Set environment variables on your server:**
   ```bash
   export AWS_ACCESS_KEY_ID="your_key_here"
   export AWS_SECRET_ACCESS_KEY="your_secret_here"
   export DB_PASSWORD="your_db_password"
   # ... etc
   ```

2. **The credentials.py file will automatically use environment variables as fallback**

## What's Included in credentials.py

### Django Secret Key
```python
SECRET_KEY = 'your-secret-key-here'
```

### Database Configuration
```python
DATABASE = {
    'NAME': 'your_database_name',
    'USER': 'your_database_user',
    'PASSWORD': 'your_database_password',
    'HOST': 'your_database_host',
    'PORT': '5432',
}
```

### Email Configuration
```python
EMAIL = {
    'HOST': 'smtp.gmail.com',
    'PORT': 587,
    'USE_TLS': True,
    'USE_SSL': False,
    'HOST_USER': 'your_email@gmail.com',
    'HOST_PASSWORD': 'your_app_password',
    'DEFAULT_FROM': 'your_email@gmail.com',
}
```

### AWS S3 Configuration
```python
AWS = {
    'ACCESS_KEY_ID': 'your_aws_access_key',
    'SECRET_ACCESS_KEY': 'your_aws_secret_key',
    'SESSION_TOKEN': '',
    'REGION_NAME': 'ap-south-1',
    'STORAGE_BUCKET_NAME': 'your-bucket-name',
}
```

### GCP Configuration
```python
GCP = {
    'STORAGE_BUCKET_NAME': 'your_gcp_bucket',
    'STORAGE_PROJECT_ID': 'your-project-id',
    'STORAGE_CREDENTIALS_PATH': 'credentials/your-credentials.json',
    'STORAGE_USE_GCS': False,
}
```

### JWT Configuration
```python
JWT = {
    'ALGORITHM': 'HS256',
    'SECRET_KEY': SECRET_KEY,  # Or use a separate key
}
```

### Admin Configuration
```python
ADMIN = {
    'URL': 'admin/',
    'EMAIL': 'admin@example.com',
    'NAME': 'Admin Name',
}
```

## Security Best Practices

### ✅ DO:
- Keep `credentials.py` in `.gitignore`
- Use environment variables in production
- Rotate credentials regularly
- Use strong, unique passwords
- Use AWS IAM roles in production (instead of access keys)
- Enable MFA on AWS accounts
- Use app-specific passwords for Gmail

### ❌ DON'T:
- Commit `credentials.py` to Git
- Share credentials via email or chat
- Use the same password across services
- Hardcode credentials in production
- Leave default/example values in production

## Troubleshooting

### Error: "credentials.py not found"
**Solution:** Copy `credentials.example.py` to `credentials.py` and fill in your credentials.

### Error: "ImportError: cannot import name 'SECRET_KEY'"
**Solution:** Make sure your `credentials.py` file has all the required variables defined.

### Credentials not updating
**Solution:** Restart your Django development server after changing `credentials.py`.

### Git is tracking credentials.py
**Solution:** 
```bash
# Remove from Git tracking (keep local file)
git rm --cached config/credentials.py

# Verify it's in .gitignore
cat .gitignore | grep credentials.py
```

## Environment Variables Priority

The credentials system checks environment variables first, then falls back to hardcoded values:

```python
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'fallback_value')
```

**Priority Order:**
1. Environment variable (highest priority)
2. Value in `credentials.py`
3. Default value (if specified)

## For Production

### Using Docker
Add to your `docker-compose.yml`:
```yaml
services:
  web:
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - DB_PASSWORD=${DB_PASSWORD}
```

### Using Systemd
Create `/etc/systemd/system/cctv.service`:
```ini
[Service]
Environment="AWS_ACCESS_KEY_ID=your_key"
Environment="AWS_SECRET_ACCESS_KEY=your_secret"
Environment="DB_PASSWORD=your_password"
```

### Using AWS Systems Manager (Recommended)
Store credentials in AWS Parameter Store and retrieve them at runtime.

## Need Help?

- Check `credentials.example.py` for the correct format
- See main project README for setup instructions
- Contact your team lead for credentials access

---

**Last Updated:** November 4, 2025  
**Security Level:** HIGH - Keep credentials.py secure!

