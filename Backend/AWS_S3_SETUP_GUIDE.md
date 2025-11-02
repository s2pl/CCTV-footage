# AWS S3 Setup Guide for CCTV Footage Storage

## 📋 Overview
This guide will help you setup AWS S3 bucket for storing CCTV footage and configure your Django application to use it.

---

## 🔑 Required Credentials & Information

To connect to AWS S3, you need the following:

1. **AWS Access Key ID** - Your AWS access key
2. **AWS Secret Access Key** - Your AWS secret key
3. **AWS Region Name** - The region where your bucket is located (e.g., `ap-south-1` for Mumbai)
4. **S3 Bucket Name** - The name of your S3 bucket
5. **AWS Session Token** (Optional) - Only needed if using temporary credentials

---

## 🚀 How to Setup S3 Bucket in AWS

### Step 1: Sign in to AWS Console
1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Sign in with your AWS account credentials
3. Make sure you're in the correct region (top-right corner)

### Step 2: Create an S3 Bucket

1. **Navigate to S3 Service**
   - Search for "S3" in the AWS Console search bar
   - Click on "S3" to open the S3 dashboard

2. **Create Bucket**
   - Click the **"Create bucket"** button
   - Enter a unique bucket name (e.g., `cctv-footage-bucket-yourcompany`)
   - Select your AWS Region (e.g., `ap-south-1` for Mumbai, India)

3. **Configure Bucket Settings**
   
   **Object Ownership:**
   - Select "ACLs disabled (recommended)"
   
   **Block Public Access:**
   - ✅ **KEEP ALL BOXES CHECKED** (Block all public access)
   - This keeps your CCTV footage private and secure
   
   **Bucket Versioning:**
   - Enable if you want to keep multiple versions of files (optional)
   
   **Default Encryption:**
   - Enable "Server-side encryption"
   - Choose "Amazon S3 managed keys (SSE-S3)" (free)
   - Or "AWS Key Management Service (SSE-KMS)" (more control, costs extra)

4. **Create Bucket**
   - Click **"Create bucket"** at the bottom
   - Your bucket is now created!

### Step 3: Configure CORS (Cross-Origin Resource Sharing)

If you plan to access videos from a web browser:

1. Go to your bucket
2. Click on the **"Permissions"** tab
3. Scroll down to **"Cross-origin resource sharing (CORS)"**
4. Click **"Edit"** and paste this configuration:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "HEAD",
            "PUT",
            "POST",
            "DELETE"
        ],
        "AllowedOrigins": [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://192.168.1.2",
            "https://yourdomain.com"
        ],
        "ExposeHeaders": [
            "ETag",
            "x-amz-server-side-encryption",
            "x-amz-request-id"
        ],
        "MaxAgeSeconds": 3600
    }
]
```

5. Click **"Save changes"**

### Step 4: Create IAM User with S3 Access

1. **Navigate to IAM Service**
   - Search for "IAM" in AWS Console
   - Click on "IAM" to open IAM dashboard

2. **Create a New User**
   - Click **"Users"** in the left sidebar
   - Click **"Create user"** button
   - Enter username (e.g., `cctv-s3-upload-user`)
   - Click **"Next"**

3. **Set Permissions**
   - Choose **"Attach policies directly"**
   - Search for `AmazonS3FullAccess` (for full S3 access)
   - OR create a custom policy with minimal permissions (see below)
   - Click **"Next"** and then **"Create user"**

4. **Create Access Keys**
   - Click on the newly created user
   - Go to **"Security credentials"** tab
   - Scroll to **"Access keys"** section
   - Click **"Create access key"**
   - Select **"Application running on AWS compute service"** or **"Other"**
   - Click **"Next"** and then **"Create access key"**
   - **⚠️ IMPORTANT:** Download the CSV file or copy the credentials NOW
   - You won't be able to see the secret key again!

### Step 5: (Recommended) Create Custom IAM Policy for Minimal Permissions

For better security, create a policy that only allows access to your specific bucket:

1. In IAM dashboard, go to **"Policies"**
2. Click **"Create policy"**
3. Click **"JSON"** tab
4. Paste this policy (replace `YOUR-BUCKET-NAME` with your actual bucket name):

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

5. Click **"Next"**
6. Name the policy (e.g., `CCTVBucketAccessPolicy`)
7. Click **"Create policy"**
8. Attach this policy to your IAM user

---

## ⚙️ Configure Your Django Application

### 1. Install Required Python Packages

Add to your `requirements.txt`:
```bash
boto3>=1.28.0
django-storages>=1.14.0
```

Install them:
```bash
pip install boto3 django-storages
```

### 2. Setup Environment Variables

Create or update your `.env` file in the project root:

```bash
# Cloud Storage Backend Selection
CLOUD_STORAGE_BACKEND=AWS  # Options: 'AWS', 'GCP', or 'BOTH'

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION_NAME=ap-south-1
AWS_STORAGE_BUCKET_NAME=cctv-footage-bucket

# Optional: For temporary credentials
# AWS_SESSION_TOKEN=your_session_token_here
```

### 3. Local Client Configuration

If using the local client (`local_client/`), create/update `.env`:

```bash
# Backend API
BACKEND_API_URL=http://your-backend-url:8000
CLIENT_TOKEN=your_client_token_here

# Cloud Storage
CLOUD_STORAGE_BACKEND=AWS

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION_NAME=ap-south-1
AWS_BUCKET_NAME=cctv-footage-bucket
```

---

## 📝 Example: Upload File to S3 with boto3

Create a utility file `Backend/utils/s3_uploader.py`:

```python
import boto3
import logging
from pathlib import Path
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings

logger = logging.getLogger(__name__)


class S3Uploader:
    """Utility class for uploading files to AWS S3"""
    
    def __init__(self):
        """Initialize S3 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION_NAME,
                config=boto3.session.Config(signature_version=settings.AWS_S3_SIGNATURE_VERSION)
            )
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            self.region = settings.AWS_REGION_NAME
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Error initializing S3 client: {str(e)}")
            raise
    
    def upload_file(
        self, 
        file_path: str, 
        s3_key: str, 
        metadata: Optional[dict] = None,
        extra_args: Optional[dict] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Upload a file to S3 bucket
        
        Args:
            file_path: Local path to file to upload
            s3_key: S3 object key (path in bucket)
            metadata: Optional metadata to attach to object
            extra_args: Optional extra arguments for upload
            
        Returns:
            Tuple of (success: bool, url: Optional[str])
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False, None
            
            # Prepare upload arguments
            upload_args = extra_args or {}
            
            # Add metadata if provided
            if metadata:
                upload_args['Metadata'] = metadata
            
            # Set content type based on file extension
            if file_path.suffix == '.mp4':
                upload_args['ContentType'] = 'video/mp4'
            elif file_path.suffix == '.avi':
                upload_args['ContentType'] = 'video/x-msvideo'
            
            # Upload file
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=upload_args
            )
            
            # Generate file URL
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            logger.info(f"Successfully uploaded {file_path} to s3://{self.bucket_name}/{s3_key}")
            return True, file_url
            
        except ClientError as e:
            logger.error(f"AWS ClientError uploading {file_path}: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error uploading {file_path} to S3: {str(e)}")
            return False, None
    
    def generate_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to private object
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL or None if error
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3 bucket
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Successfully deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {s3_key} from S3: {str(e)}")
            return False
    
    def list_files(self, prefix: str = '') -> list:
        """
        List files in bucket with given prefix
        
        Args:
            prefix: S3 key prefix to filter results
            
        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
        except Exception as e:
            logger.error(f"Error listing files in S3: {str(e)}")
            return []


# Example usage:
def upload_cctv_recording(local_file_path: str, camera_id: str, timestamp: str):
    """
    Example function to upload CCTV recording
    
    Args:
        local_file_path: Path to local video file
        camera_id: Camera identifier
        timestamp: Recording timestamp
    """
    uploader = S3Uploader()
    
    # Create S3 key with organized structure
    s3_key = f"recordings/{camera_id}/{timestamp.split('T')[0]}/{Path(local_file_path).name}"
    
    # Add metadata
    metadata = {
        'camera_id': camera_id,
        'timestamp': timestamp,
        'upload_date': str(datetime.now())
    }
    
    # Upload file
    success, url = uploader.upload_file(
        file_path=local_file_path,
        s3_key=s3_key,
        metadata=metadata
    )
    
    if success:
        print(f"File uploaded successfully!")
        print(f"URL: {url}")
        
        # Generate presigned URL for secure access
        presigned_url = uploader.generate_presigned_url(s3_key, expiration=7200)
        print(f"Presigned URL (valid for 2 hours): {presigned_url}")
    else:
        print("Upload failed!")
```

---

## 🧪 Test Your S3 Connection

Create a test script `Backend/test_s3_connection.py`:

```python
import os
import sys
from pathlib import Path

# Add project to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

import boto3
from django.conf import settings
from botocore.exceptions import ClientError, NoCredentialsError


def test_s3_connection():
    """Test AWS S3 connection and credentials"""
    print("=" * 60)
    print("Testing AWS S3 Connection")
    print("=" * 60)
    
    # Check if credentials are set
    print("\n1. Checking AWS Credentials...")
    if not settings.AWS_ACCESS_KEY_ID:
        print("❌ AWS_ACCESS_KEY_ID is not set!")
        return False
    if not settings.AWS_SECRET_ACCESS_KEY:
        print("❌ AWS_SECRET_ACCESS_KEY is not set!")
        return False
    
    print(f"✅ AWS Access Key ID: {settings.AWS_ACCESS_KEY_ID[:10]}...")
    print(f"✅ Region: {settings.AWS_REGION_NAME}")
    print(f"✅ Bucket Name: {settings.AWS_STORAGE_BUCKET_NAME}")
    
    # Test S3 connection
    print("\n2. Testing S3 Connection...")
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION_NAME
        )
        
        # Try to list objects (just to verify connection)
        response = s3_client.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            MaxKeys=1
        )
        
        print("✅ Successfully connected to S3!")
        print(f"✅ Bucket '{settings.AWS_STORAGE_BUCKET_NAME}' is accessible")
        
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not found or invalid!")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ Bucket '{settings.AWS_STORAGE_BUCKET_NAME}' does not exist!")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to bucket '{settings.AWS_STORAGE_BUCKET_NAME}'!")
            print("   Check your IAM permissions.")
        else:
            print(f"❌ AWS Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_s3_connection()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ AWS S3 is configured correctly!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ AWS S3 configuration has issues. Please fix them.")
        print("=" * 60)
        sys.exit(1)
```

Run the test:
```bash
cd Backend
python test_s3_connection.py
```

---

## 🔒 Security Best Practices

1. **Never commit credentials to Git**
   - Always use `.env` files
   - Add `.env` to `.gitignore`

2. **Use IAM roles when possible**
   - If running on EC2, use IAM roles instead of access keys
   - More secure and no need to manage credentials

3. **Restrict IAM permissions**
   - Only give minimum required permissions
   - Use bucket-specific policies

4. **Enable bucket encryption**
   - Use SSE-S3 or SSE-KMS encryption

5. **Enable S3 logging**
   - Track who accesses your bucket

6. **Use presigned URLs**
   - For temporary access to private files
   - Set appropriate expiration times

7. **Enable versioning**
   - Protect against accidental deletion

---

## 📊 Cost Considerations

### S3 Pricing (ap-south-1 - Mumbai Region)

- **Storage**: ~$0.023 per GB/month for first 50 TB
- **PUT/POST requests**: ~$0.005 per 1,000 requests
- **GET requests**: ~$0.0004 per 1,000 requests
- **Data transfer OUT**: First 1 GB free, then ~$0.109 per GB

### Example Cost Calculation

If you're recording:
- 10 cameras
- 24 hours/day
- 1 MB per second video quality
- Keep 30 days of footage

**Storage**: 10 cameras × 86,400 seconds × 1 MB × 30 days ≈ 25,920 GB
**Cost**: 25,920 GB × $0.023 = **~$596/month**

💡 **Tip**: Use lifecycle policies to automatically move old footage to cheaper storage tiers like S3 Glacier.

---

## 🆘 Troubleshooting

### Error: "NoCredentialsError"
**Solution**: Check that AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set in .env

### Error: "AccessDenied"
**Solution**: Check IAM user permissions. Ensure the user has S3 access to the specific bucket.

### Error: "NoSuchBucket"
**Solution**: Verify the bucket name is correct and exists in the specified region.

### Error: "SignatureDoesNotMatch"
**Solution**: Check that your secret access key is correct. Re-generate if needed.

### Slow uploads
**Solution**: 
- Use multipart upload for large files
- Check your internet connection
- Consider using AWS Transfer Acceleration

---

## 📚 Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Django Storages Documentation](https://django-storages.readthedocs.io/)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

## ✅ Checklist

- [ ] AWS account created
- [ ] S3 bucket created with appropriate settings
- [ ] IAM user created with S3 permissions
- [ ] Access keys generated and saved securely
- [ ] `.env` file configured with AWS credentials
- [ ] `boto3` and `django-storages` installed
- [ ] S3 connection tested successfully
- [ ] CORS configured (if needed for web access)
- [ ] Encryption enabled on bucket
- [ ] Cost monitoring set up

---

Need help? Contact your DevOps team or AWS support!

