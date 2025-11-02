# AWS S3 Integration Summary

## 📝 Overview

This document summarizes the AWS S3 integration changes made to your CCTV footage storage system. Your system now supports both AWS S3 and Google Cloud Storage (GCP), with the ability to choose between them via configuration.

---

## ✅ Files Created/Modified

### New Files Created

1. **`Backend/AWS_S3_SETUP_GUIDE.md`**
   - Comprehensive guide on setting up AWS S3
   - Step-by-step bucket creation instructions
   - IAM user setup and permissions
   - Cost estimates and best practices
   - Troubleshooting guide

2. **`Backend/S3_QUICK_REFERENCE.md`**
   - Quick reference for common S3 operations
   - Code examples
   - Common issues and solutions
   - Setup checklist

3. **`Backend/utils/s3_uploader.py`**
   - S3Uploader class for file operations
   - Methods: upload, download, delete, list files
   - Presigned URL generation
   - CCTV-specific upload helpers

4. **`Backend/utils/__init__.py`**
   - Makes utils a proper Python package

5. **`Backend/test_s3_connection.py`**
   - Test script to verify S3 configuration
   - Checks credentials, bucket access, permissions
   - Automated testing of all S3 operations

6. **`Backend/env.s3.template`**
   - Template for Backend .env configuration
   - Shows all required AWS environment variables

7. **`Backend/local_client/env.s3.template`**
   - Template for Local Client .env configuration
   - Client-specific AWS configuration

8. **`Backend/S3_INTEGRATION_SUMMARY.md`** (this file)
   - Summary of all changes
   - What's needed next

### Modified Files

1. **`Backend/config/settings.py`**
   - Added AWS S3 configuration section
   - Added `CLOUD_STORAGE_BACKEND` selector
   - Kept GCP configuration for backward compatibility
   - Environment variable support for all AWS settings

2. **`Backend/local_client/config.py`**
   - Added AWS S3 configuration
   - Updated validation to check AWS credentials
   - Support for multi-cloud storage backends

3. **`Backend/requirements.txt`**
   - Added `boto3>=1.28.0` - AWS SDK
   - Added `botocore>=1.31.0` - AWS core library
   - Added `s3transfer>=0.7.0` - S3 transfer utilities
   - Added `django-storages>=1.14.0` - Django storage backends

---

## 🔑 What You Need from AWS

### 1. AWS Account
- Sign up at https://aws.amazon.com/
- Free tier available (12 months, 5GB storage, 20,000 GET requests, 2,000 PUT requests per month)

### 2. S3 Bucket
- Bucket Name: Choose a globally unique name (e.g., `cctv-footage-yourcompany-2024`)
- Region: Choose closest to your location (e.g., `ap-south-1` for Mumbai, India)
- Encryption: Enable Server-Side Encryption (SSE-S3)
- Public Access: Block all public access (keep private)

### 3. IAM User Credentials
You need to create an IAM user and get:
- **AWS Access Key ID** (e.g., `AKIAIOSFODNN7EXAMPLE`)
- **AWS Secret Access Key** (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

### 4. IAM Permissions
The IAM user needs these S3 permissions on your bucket:
- `s3:ListBucket` - List bucket contents
- `s3:GetObject` - Read/download files
- `s3:PutObject` - Upload files
- `s3:DeleteObject` - Delete files
- `s3:GetObjectAcl` - Get file permissions
- `s3:PutObjectAcl` - Set file permissions

---

## 🎯 Step-by-Step Setup

### Step 1: Install Dependencies
```bash
cd Backend
pip install -r requirements.txt
```

### Step 2: Create S3 Bucket
1. Go to AWS Console → S3
2. Click "Create bucket"
3. Name: `cctv-footage-yourcompany`
4. Region: `ap-south-1` (or your preferred region)
5. Block all public access: ✅ (checked)
6. Enable encryption: ✅ (SSE-S3)
7. Click "Create bucket"

### Step 3: Create IAM User
1. Go to AWS Console → IAM → Users
2. Click "Create user"
3. Username: `cctv-s3-uploader`
4. Permissions: Attach custom policy (see guide) or `AmazonS3FullAccess`
5. Create user

### Step 4: Generate Access Keys
1. Click on user → Security credentials
2. Create access key
3. Select "Application running outside AWS"
4. Save both Access Key ID and Secret Access Key

### Step 5: Configure Environment Variables
Create/update `.env` file in `Backend/`:
```bash
# Copy template
cp env.s3.template .env

# Edit .env and add your credentials:
CLOUD_STORAGE_BACKEND=AWS
AWS_ACCESS_KEY_ID=your_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION_NAME=ap-south-1
AWS_STORAGE_BUCKET_NAME=cctv-footage-yourcompany
```

For local client, also update `Backend/local_client/.env`:
```bash
cd Backend/local_client
cp env.s3.template .env
# Edit with same credentials
```

### Step 6: Test Connection
```bash
cd Backend
python test_s3_connection.py
```

You should see:
```
✅ AWS S3 Configuration is Valid!
```

---

## 💻 How to Use in Your Code

### Option 1: Use the S3Uploader Utility

```python
from utils.s3_uploader import S3Uploader

# Initialize uploader
uploader = S3Uploader()

# Upload a file
success, url = uploader.upload_file(
    file_path='recordings/video.mp4',
    s3_key='recordings/camera-1/2024-11-02/video.mp4',
    metadata={'camera_id': 'camera-1'}
)

if success:
    print(f"Video uploaded! URL: {url}")
    
    # Generate presigned URL for viewing
    view_url = uploader.generate_presigned_url(
        s3_key='recordings/camera-1/2024-11-02/video.mp4',
        expiration=7200  # Valid for 2 hours
    )
    print(f"View URL: {view_url}")
```

### Option 2: Use CCTV Helper Function

```python
from utils.s3_uploader import upload_cctv_recording

# Upload with automatic organization
success, url = upload_cctv_recording(
    local_file_path='recordings/video.mp4',
    camera_id='camera-123',
    timestamp='2024-11-02T14:30:00',
    recording_id='rec-456'
)
```

### Option 3: Direct boto3 Usage

```python
import boto3
from django.conf import settings

s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION_NAME
)

# Upload
s3.upload_file(
    'local_file.mp4',
    settings.AWS_STORAGE_BUCKET_NAME,
    'recordings/file.mp4'
)
```

---

## ⚙️ Configuration Options

### In `settings.py`:

```python
# Storage backend selection
CLOUD_STORAGE_BACKEND = 'AWS'  # or 'GCP' or 'BOTH'

# AWS credentials
AWS_ACCESS_KEY_ID = 'your_key'
AWS_SECRET_ACCESS_KEY = 'your_secret'
AWS_REGION_NAME = 'ap-south-1'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'

# Behavior settings
AWS_STORAGE_CLEANUP_LOCAL = True   # Delete local files after upload
AWS_STORAGE_AUTO_UPLOAD = True     # Auto-upload recordings
AWS_STORAGE_UPLOAD_TIMEOUT = 600   # 10 minutes timeout
AWS_PRESIGNED_URL_EXPIRATION = 7200  # 2 hours
```

---

## 🔄 Migration from GCP to AWS

If you want to switch from GCP to AWS:

### 1. Update Environment Variable
```bash
# In .env file
CLOUD_STORAGE_BACKEND=AWS  # Change from GCP to AWS
```

### 2. Transfer Existing Data (Optional)
If you have existing footage in GCP:

```python
# Transfer script example
from google.cloud import storage as gcp_storage
from utils.s3_uploader import S3Uploader

# Download from GCP and upload to S3
gcp_client = gcp_storage.Client()
s3_uploader = S3Uploader()

bucket = gcp_client.bucket('cctv_feed')
blobs = bucket.list_blobs()

for blob in blobs:
    # Download from GCP
    local_file = f'/tmp/{blob.name}'
    blob.download_to_filename(local_file)
    
    # Upload to S3
    success, url = s3_uploader.upload_file(local_file, blob.name)
    print(f"Transferred: {blob.name}")
```

### 3. Use Both (Redundancy)
```bash
# In .env
CLOUD_STORAGE_BACKEND=BOTH
```
This will upload to both AWS S3 and GCP simultaneously for redundancy.

---

## 💰 Cost Considerations

### Storage Costs (ap-south-1 region)
- **Storage**: ~$0.023 per GB/month
- **PUT requests**: ~$0.005 per 1,000 requests
- **GET requests**: ~$0.0004 per 1,000 requests
- **Data transfer out**: $0.109 per GB (after first 1 GB free)

### Example Monthly Cost
**Scenario**: 10 cameras, 24/7 recording, 1MB/s bitrate, 30 days retention
- **Storage**: 25,920 GB × $0.023 = $596/month
- **Uploads**: ~259,200 files × $0.005/1000 = $1.30/month
- **Views**: Minimal (depends on usage)
- **Total**: ~$600/month

### Cost Optimization Tips
1. **Use S3 Lifecycle Policies**: Move old footage to Glacier after 7 days (saves 90%)
2. **Compress videos**: Use H.265 codec instead of H.264 (saves 30-50% space)
3. **Delete old footage**: Set retention policy (e.g., keep only 30 days)
4. **Use S3 Intelligent-Tiering**: Automatic cost optimization
5. **Monitor usage**: Set up AWS Cost Explorer alerts

---

## 🔒 Security Best Practices

1. **Never commit credentials**: Keep `.env` in `.gitignore`
2. **Use IAM roles on EC2**: If running on AWS, use roles instead of keys
3. **Rotate keys regularly**: Change access keys every 90 days
4. **Minimal permissions**: Only grant necessary S3 permissions
5. **Enable MFA**: Protect your AWS account with multi-factor auth
6. **Encrypt at rest**: Use SSE-S3 or SSE-KMS encryption
7. **Use HTTPS**: All S3 transfers should use SSL/TLS
8. **Monitor access**: Enable S3 access logging and CloudTrail

---

## 🧪 Testing Checklist

Before deploying to production:

- [ ] Install all dependencies (`pip install -r requirements.txt`)
- [ ] Configure `.env` with AWS credentials
- [ ] Run `python test_s3_connection.py` - passes all tests
- [ ] Upload a test video file successfully
- [ ] Generate presigned URL and verify it works
- [ ] Delete test files successfully
- [ ] Check AWS Cost Explorer for expected costs
- [ ] Set up billing alerts in AWS
- [ ] Configure CORS if accessing from browser
- [ ] Set up lifecycle policies for old files
- [ ] Document bucket name and region for team
- [ ] Test failover (if using BOTH backends)

---

## 📚 Documentation Files

1. **`AWS_S3_SETUP_GUIDE.md`** - Full detailed setup guide
2. **`S3_QUICK_REFERENCE.md`** - Quick reference and examples
3. **`S3_INTEGRATION_SUMMARY.md`** - This file, overview of changes
4. **`test_s3_connection.py`** - Automated testing script
5. **`utils/s3_uploader.py`** - Main S3 utility code

---

## 🆘 Troubleshooting

### Issue: "NoCredentialsError"
**Fix**: Set AWS credentials in `.env` file

### Issue: "AccessDenied"
**Fix**: Check IAM user has S3 permissions for the bucket

### Issue: "NoSuchBucket"
**Fix**: Verify bucket name is correct and exists

### Issue: Import error for utils.s3_uploader
**Fix**: Make sure you're in the right directory and Django is set up:
```bash
export DJANGO_SETTINGS_MODULE=config.settings
python
>>> from utils.s3_uploader import S3Uploader
```

### Issue: Slow uploads
**Fix**: 
- Check internet speed
- boto3 automatically uses multipart upload for large files
- Consider S3 Transfer Acceleration (additional cost)

---

## 📞 Support

- **AWS Support**: https://console.aws.amazon.com/support/
- **boto3 Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **S3 Pricing**: https://aws.amazon.com/s3/pricing/

---

## 🎉 Next Steps

1. ✅ Complete AWS S3 setup (follow AWS_S3_SETUP_GUIDE.md)
2. ✅ Test connection (`python test_s3_connection.py`)
3. 🔄 Update your recording upload code to use S3Uploader
4. 🔄 Set up S3 lifecycle policies to manage costs
5. 🔄 Configure monitoring and alerting
6. 🔄 Document for your team
7. 🔄 Deploy to production

---

**Integration completed on**: November 2, 2024
**Version**: 1.0
**Supported backends**: AWS S3, Google Cloud Storage (GCP)

