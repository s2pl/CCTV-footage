# AWS S3 Quick Reference

## 🚀 Quick Start

### 1. Install Required Packages
```bash
cd Backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the template and fill in your AWS credentials:
```bash
# For Django Backend
cp env.s3.template .env

# For Local Client
cp local_client/env.s3.template local_client/.env
```

Edit `.env` file:
```bash
CLOUD_STORAGE_BACKEND=AWS
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION_NAME=ap-south-1
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

### 3. Test Connection
```bash
cd Backend
python test_s3_connection.py
```

---

## 📋 What You Need

### Required AWS Credentials
1. **AWS Access Key ID** - From IAM User
2. **AWS Secret Access Key** - From IAM User
3. **S3 Bucket Name** - Your unique bucket name
4. **AWS Region** - e.g., `ap-south-1` (Mumbai)

### Required IAM Permissions
Your IAM user needs these S3 permissions:
- `s3:ListBucket` - List objects in bucket
- `s3:GetObject` - Download files
- `s3:PutObject` - Upload files
- `s3:DeleteObject` - Delete files
- `s3:GetObjectAcl` - Get file permissions
- `s3:PutObjectAcl` - Set file permissions

---

## 🔧 Configuration Files Updated

### 1. `Backend/config/settings.py`
Added AWS S3 configuration:
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `AWS_REGION_NAME` - AWS region (default: ap-south-1)
- `AWS_STORAGE_BUCKET_NAME` - S3 bucket name
- `AWS_S3_SIGNATURE_VERSION` - Signature version (s3v4)
- `AWS_PRESIGNED_URL_EXPIRATION` - URL expiration (7200s = 2 hours)

### 2. `Backend/local_client/config.py`
Added AWS S3 configuration for local client:
- `CLOUD_STORAGE_BACKEND` - Select 'AWS', 'GCP', or 'BOTH'
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - Credentials
- `AWS_REGION_NAME`, `AWS_BUCKET_NAME` - Bucket info

### 3. `Backend/requirements.txt`
Added required packages:
- `boto3>=1.28.0` - AWS SDK for Python
- `botocore>=1.31.0` - Low-level AWS client
- `s3transfer>=0.7.0` - S3 transfer manager
- `django-storages>=1.14.0` - Django storage backends

---

## 💻 Usage Examples

### Upload a File
```python
from utils.s3_uploader import S3Uploader

uploader = S3Uploader()
success, url = uploader.upload_file(
    file_path='path/to/video.mp4',
    s3_key='recordings/camera1/2024-01-01/video.mp4',
    metadata={'camera_id': 'camera1', 'timestamp': '2024-01-01T10:00:00'}
)

if success:
    print(f"Uploaded! URL: {url}")
```

### Upload CCTV Recording
```python
from utils.s3_uploader import upload_cctv_recording

success, url = upload_cctv_recording(
    local_file_path='recording.mp4',
    camera_id='camera-123',
    timestamp='2024-01-01T10:00:00',
    recording_id='rec-456'
)
```

### Generate Presigned URL
```python
from utils.s3_uploader import get_recording_url

# Get URL valid for 2 hours
url = get_recording_url(
    s3_key='recordings/camera1/2024-01-01/video.mp4',
    expiration=7200
)
print(f"Access URL: {url}")
```

### Delete a File
```python
from utils.s3_uploader import S3Uploader

uploader = S3Uploader()
success = uploader.delete_file('recordings/camera1/2024-01-01/video.mp4')
```

### List Files
```python
from utils.s3_uploader import S3Uploader

uploader = S3Uploader()
files = uploader.list_files(prefix='recordings/camera1/')

for file in files:
    print(f"{file['key']} - {file['size']} bytes")
```

---

## 🎯 Step-by-Step AWS Setup

### Step 1: Create S3 Bucket
1. Go to [AWS S3 Console](https://console.aws.amazon.com/s3/)
2. Click "Create bucket"
3. Enter bucket name (e.g., `cctv-footage-yourcompany`)
4. Select region (e.g., `ap-south-1` for Mumbai)
5. **Block all public access** (keep data private)
6. Enable "Server-side encryption" (SSE-S3)
7. Click "Create bucket"

### Step 2: Create IAM User
1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click "Users" → "Create user"
3. Enter username (e.g., `cctv-s3-uploader`)
4. Click "Next"

### Step 3: Attach Permissions
1. Select "Attach policies directly"
2. Create custom policy (see below) OR
3. Attach `AmazonS3FullAccess` (less secure but easier)

### Step 4: Create Access Keys
1. Click on the user → "Security credentials"
2. Scroll to "Access keys" → "Create access key"
3. Select "Application running outside AWS"
4. Click "Next" → "Create access key"
5. **SAVE THE KEYS!** (You won't see the secret again)

---

## 🔒 Minimal IAM Policy (Recommended)

Replace `YOUR-BUCKET-NAME` with your actual bucket name:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME",
                "arn:aws:s3:::YOUR-BUCKET-NAME/*"
            ]
        }
    ]
}
```

---

## 🧪 Testing

### Test S3 Connection
```bash
cd Backend
python test_s3_connection.py
```

### Test Upload
```python
from utils.s3_uploader import S3Uploader

uploader = S3Uploader()
success, url = uploader.upload_file(
    'test.txt',
    'test/test.txt'
)
print(f"Success: {success}, URL: {url}")
```

---

## 💰 Cost Estimation

### Pricing (ap-south-1 - Mumbai)
- **Storage**: ~$0.023 per GB/month
- **Upload (PUT)**: ~$0.005 per 1,000 requests
- **Download (GET)**: ~$0.0004 per 1,000 requests
- **Data Transfer OUT**: $0.109 per GB (after first 1 GB free)

### Example Cost
**10 cameras, 24/7 recording, 1MB/s bitrate, 30 days:**
- Storage: ~25,920 GB × $0.023 = **~$596/month**
- Uploads: ~259,200 files × $0.005/1000 = **~$1.30/month**
- **Total: ~$600/month**

💡 **Tip**: Use S3 Lifecycle policies to move old footage to cheaper storage (S3 Glacier) to reduce costs by up to 90%!

---

## ⚠️ Common Issues

### Error: "NoCredentialsError"
**Solution**: Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`

### Error: "AccessDenied"
**Solution**: Check IAM permissions. User needs S3 access to the bucket.

### Error: "NoSuchBucket"
**Solution**: Verify bucket name in `AWS_STORAGE_BUCKET_NAME` is correct.

### Error: "InvalidAccessKeyId"
**Solution**: Check your access key ID is correct.

### Error: "SignatureDoesNotMatch"
**Solution**: Your secret access key is wrong. Re-generate keys.

### Slow Uploads
**Solutions**:
- Check internet speed
- Use multipart upload for large files (boto3 does this automatically)
- Enable S3 Transfer Acceleration (costs extra)

---

## 📚 Resources

- **Full Setup Guide**: `Backend/AWS_S3_SETUP_GUIDE.md`
- **AWS S3 Docs**: https://docs.aws.amazon.com/s3/
- **Boto3 Docs**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **Django Storages**: https://django-storages.readthedocs.io/

---

## ✅ Quick Checklist

Before going to production:

- [ ] S3 bucket created
- [ ] Bucket encryption enabled (SSE-S3 or SSE-KMS)
- [ ] Public access blocked
- [ ] IAM user created with minimal permissions
- [ ] Access keys generated and saved securely
- [ ] `.env` file configured (and NOT committed to git!)
- [ ] Connection test passed
- [ ] Test file upload/download works
- [ ] CORS configured (if accessing from browser)
- [ ] Cost monitoring set up in AWS
- [ ] Lifecycle policy configured for old files
- [ ] Backup strategy in place

---

## 🆘 Need Help?

1. Check the full guide: `Backend/AWS_S3_SETUP_GUIDE.md`
2. Run the test script: `python test_s3_connection.py`
3. Check AWS CloudWatch logs for detailed errors
4. Contact your DevOps team or AWS support

---

**Last Updated**: November 2024

