"""
Test AWS S3 Connection
Run this script to verify your AWS S3 configuration
"""
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
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def test_s3_connection():
    """Test AWS S3 connection and credentials"""
    
    print_header("AWS S3 Connection Test")
    
    # Step 1: Check if credentials are set
    print("\n📋 Step 1: Checking AWS Credentials...")
    
    if not hasattr(settings, 'AWS_ACCESS_KEY_ID') or not settings.AWS_ACCESS_KEY_ID:
        print_error("AWS_ACCESS_KEY_ID is not set in settings!")
        print_info("Set AWS_ACCESS_KEY_ID in your .env file")
        return False
    
    if not hasattr(settings, 'AWS_SECRET_ACCESS_KEY') or not settings.AWS_SECRET_ACCESS_KEY:
        print_error("AWS_SECRET_ACCESS_KEY is not set in settings!")
        print_info("Set AWS_SECRET_ACCESS_KEY in your .env file")
        return False
    
    if not hasattr(settings, 'AWS_STORAGE_BUCKET_NAME') or not settings.AWS_STORAGE_BUCKET_NAME:
        print_error("AWS_STORAGE_BUCKET_NAME is not set in settings!")
        print_info("Set AWS_STORAGE_BUCKET_NAME in your .env file")
        return False
    
    print_success(f"AWS Access Key ID: {settings.AWS_ACCESS_KEY_ID[:10]}...")
    print_success(f"AWS Region: {settings.AWS_REGION_NAME}")
    print_success(f"AWS Bucket Name: {settings.AWS_STORAGE_BUCKET_NAME}")
    
    # Check cloud storage backend
    if hasattr(settings, 'CLOUD_STORAGE_BACKEND'):
        print_info(f"Cloud Storage Backend: {settings.CLOUD_STORAGE_BACKEND}")
    
    # Step 2: Test boto3 import
    print("\n📦 Step 2: Checking boto3 installation...")
    try:
        import boto3
        import botocore
        print_success(f"boto3 version: {boto3.__version__}")
        print_success(f"botocore version: {botocore.__version__}")
    except ImportError as e:
        print_error(f"boto3 is not installed: {str(e)}")
        print_info("Run: pip install boto3")
        return False
    
    # Step 3: Test S3 connection
    print("\n🔌 Step 3: Testing S3 Connection...")
    try:
        session_config = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
            'region_name': settings.AWS_REGION_NAME,
        }
        
        # Add session token if provided
        if hasattr(settings, 'AWS_SESSION_TOKEN') and settings.AWS_SESSION_TOKEN:
            session_config['aws_session_token'] = settings.AWS_SESSION_TOKEN
            print_info("Using AWS Session Token (temporary credentials)")
        
        s3_client = boto3.client('s3', **session_config)
        
        print_success("S3 client created successfully!")
        
    except (NoCredentialsError, PartialCredentialsError) as e:
        print_error(f"AWS credentials error: {str(e)}")
        print_info("Check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return False
    except Exception as e:
        print_error(f"Error creating S3 client: {str(e)}")
        return False
    
    # Step 4: Test bucket access
    print("\n🪣 Step 4: Testing Bucket Access...")
    try:
        # Try to list objects (just to verify connection and permissions)
        response = s3_client.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            MaxKeys=1
        )
        
        print_success(f"Successfully connected to bucket '{settings.AWS_STORAGE_BUCKET_NAME}'!")
        
        # Check if bucket has any objects
        if 'Contents' in response:
            print_info(f"Bucket contains files")
        else:
            print_info("Bucket is empty or no files in root")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'NoSuchBucket':
            print_error(f"Bucket '{settings.AWS_STORAGE_BUCKET_NAME}' does not exist!")
            print_info("Create the bucket in AWS S3 Console or check the bucket name")
        elif error_code == 'AccessDenied':
            print_error(f"Access denied to bucket '{settings.AWS_STORAGE_BUCKET_NAME}'!")
            print_info("Check your IAM user permissions:")
            print_info("  - s3:ListBucket")
            print_info("  - s3:GetObject")
            print_info("  - s3:PutObject")
        elif error_code == 'InvalidAccessKeyId':
            print_error("Invalid AWS Access Key ID!")
            print_info("Check your AWS_ACCESS_KEY_ID in .env file")
        elif error_code == 'SignatureDoesNotMatch':
            print_error("AWS Secret Access Key is incorrect!")
            print_info("Check your AWS_SECRET_ACCESS_KEY in .env file")
        else:
            print_error(f"AWS Error ({error_code}): {e}")
        
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False
    
    # Step 5: Test permissions
    print("\n🔐 Step 5: Testing Permissions...")
    test_key = "test/connection_test.txt"
    test_content = b"This is a test file created by test_s3_connection.py"
    
    # Test write permission
    try:
        s3_client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key,
            Body=test_content
        )
        print_success("Write permission: ✓ (s3:PutObject)")
        
        # Test read permission
        s3_client.get_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key
        )
        print_success("Read permission: ✓ (s3:GetObject)")
        
        # Test delete permission
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key
        )
        print_success("Delete permission: ✓ (s3:DeleteObject)")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print_error(f"Permission error ({error_code}): {e}")
        print_info("Your IAM user needs these permissions:")
        print_info("  - s3:PutObject (to upload files)")
        print_info("  - s3:GetObject (to download files)")
        print_info("  - s3:DeleteObject (to delete files)")
    except Exception as e:
        print_error(f"Permission test error: {str(e)}")
    
    # Step 6: Test presigned URL generation
    print("\n🔗 Step 6: Testing Presigned URL Generation...")
    try:
        # Upload a test file first
        s3_client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key,
            Body=test_content
        )
        
        # Generate presigned URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': test_key
            },
            ExpiresIn=3600
        )
        
        print_success("Presigned URL generation: ✓")
        print_info(f"Sample URL (expires in 1 hour):")
        print_info(f"  {url[:80]}...")
        
        # Clean up test file
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key
        )
        
    except Exception as e:
        print_error(f"Presigned URL generation error: {str(e)}")
    
    return True


def print_summary():
    """Print configuration summary"""
    print_header("Configuration Summary")
    
    config_items = [
        ("Storage Backend", getattr(settings, 'CLOUD_STORAGE_BACKEND', 'Not set')),
        ("AWS Region", getattr(settings, 'AWS_REGION_NAME', 'Not set')),
        ("S3 Bucket", getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')),
        ("Signature Version", getattr(settings, 'AWS_S3_SIGNATURE_VERSION', 'Not set')),
        ("Auto Upload", getattr(settings, 'AWS_STORAGE_AUTO_UPLOAD', 'Not set')),
        ("Cleanup Local", getattr(settings, 'AWS_STORAGE_CLEANUP_LOCAL', 'Not set')),
        ("Upload Timeout", f"{getattr(settings, 'AWS_STORAGE_UPLOAD_TIMEOUT', 'Not set')}s"),
        ("Presigned URL Expiration", f"{getattr(settings, 'AWS_PRESIGNED_URL_EXPIRATION', 'Not set')}s"),
    ]
    
    print("\n📝 Current Settings:")
    for name, value in config_items:
        print(f"  • {name:.<30} {value}")


def main():
    """Main test function"""
    try:
        success = test_s3_connection()
        
        if success:
            print_summary()
            print_header("✅ AWS S3 Configuration is Valid!")
            print("\n🎉 Your application is ready to use AWS S3 storage!")
            print("\nNext steps:")
            print("  1. Update your recording upload code to use S3")
            print("  2. Test uploading a video file")
            print("  3. Monitor your S3 costs in AWS Console")
            print("  4. Set up lifecycle policies for old recordings")
            print("\n")
            return 0
        else:
            print_header("❌ AWS S3 Configuration Has Issues")
            print("\n🔧 Please fix the errors above and try again.")
            print("\nCommon solutions:")
            print("  1. Check your .env file has correct AWS credentials")
            print("  2. Verify the bucket name is correct")
            print("  3. Ensure IAM user has proper S3 permissions")
            print("  4. Check if the bucket is in the correct region")
            print("\n📚 See AWS_S3_SETUP_GUIDE.md for detailed instructions")
            print("\n")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

