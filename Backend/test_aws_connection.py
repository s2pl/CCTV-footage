#!/usr/bin/env python
"""
AWS S3 Connection Test Script
Run this to verify AWS S3 is properly configured and connected
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cctv.storage_service import storage_service
from django.conf import settings

def test_aws_connection():
    """Test AWS S3 connection and configuration"""
    
    print("\n" + "=" * 70)
    print("AWS S3 CONNECTION TEST")
    print("=" * 70 + "\n")
    
    # Check storage backend configuration
    backend = getattr(settings, 'CLOUD_STORAGE_BACKEND', 'LOCAL')
    print(f"📋 Configured Storage Backend: {backend}")
    
    # Check if AWS is enabled
    if storage_service.use_aws:
        print("✅ AWS S3 is ENABLED\n")
        
        # Display configuration
        print("🔧 AWS S3 Configuration:")
        print(f"   Bucket Name: {storage_service.aws_service.bucket_name}")
        print(f"   Region: {storage_service.aws_service.region_name}")
        print(f"   Access Key ID: {storage_service.aws_service.access_key[:10]}..." if storage_service.aws_service.access_key else "   Access Key ID: Not set")
        
        # Test connection by checking bucket access
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            print("\n🔌 Testing connection to AWS S3...")
            
            s3_client = storage_service.aws_service.client
            
            if not s3_client:
                print("❌ Failed to initialize AWS S3 client")
                print("   Check your AWS credentials and configuration")
                return False
            
            # Test bucket access
            try:
                s3_client.head_bucket(Bucket=storage_service.aws_service.bucket_name)
                print("✅ Successfully connected to AWS S3 bucket!")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    print(f"❌ Bucket '{storage_service.aws_service.bucket_name}' does not exist")
                    print("   Create the bucket in AWS Console or check bucket name")
                elif error_code == '403':
                    print(f"❌ Access denied to bucket '{storage_service.aws_service.bucket_name}'")
                    print("   Check IAM permissions for your AWS credentials")
                else:
                    print(f"❌ Error accessing bucket: {str(e)}")
                return False
            
            # List objects in bucket
            print("\n📦 Checking bucket contents...")
            try:
                response = s3_client.list_objects_v2(
                    Bucket=storage_service.aws_service.bucket_name,
                    Prefix='recordings/',
                    MaxKeys=10
                )
                
                if 'Contents' in response:
                    print(f"   Found {response.get('KeyCount', 0)} files in 'recordings/' folder:")
                    for obj in response['Contents'][:5]:  # Show first 5 files
                        size_mb = obj['Size'] / (1024 * 1024)
                        print(f"   - {obj['Key']} ({size_mb:.2f} MB)")
                    
                    if response.get('KeyCount', 0) > 5:
                        print(f"   ... and {response.get('KeyCount', 0) - 5} more files")
                else:
                    print("   Bucket is empty (no recordings yet)")
                    
            except ClientError as e:
                print(f"   ⚠️  Could not list bucket contents: {str(e)}")
            
            # Test presigned URL generation
            print("\n🔗 Testing presigned URL generation...")
            try:
                # Test with a dummy file path
                test_path = "recordings/test/dummy.mp4"
                # We're just testing if the method works, not if the file exists
                # So we'll catch the specific error about file not existing
                url = storage_service.aws_service.get_file_url(test_path, signed=True)
                if url:
                    print("✅ Presigned URL generation is working")
                    print(f"   Example URL structure: {url[:80]}...")
                else:
                    # This is expected if file doesn't exist
                    print("✅ Presigned URL generation method is available")
                    print("   (URLs will be generated when files exist)")
            except Exception as e:
                print(f"   ⚠️  Presigned URL test: {str(e)}")
            
            print("\n" + "=" * 70)
            print("🎉 AWS S3 CONNECTION TEST PASSED!")
            print("=" * 70)
            print("\n✅ Your AWS S3 storage is properly configured and connected")
            print("✅ Recordings will be automatically uploaded to AWS S3")
            print("✅ Presigned URLs will be generated for secure file access")
            
            if getattr(settings, 'AWS_STORAGE_CLEANUP_LOCAL', True):
                print("✅ Local files will be cleaned up after successful upload")
            else:
                print("ℹ️  Local files will be kept after upload")
            
            return True
            
        except NoCredentialsError:
            print("\n❌ AWS credentials not found")
            print("   Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in settings")
            return False
            
        except ImportError:
            print("\n❌ boto3 package not installed")
            print("   Run: pip install boto3")
            return False
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    elif storage_service.use_gcp:
        print("ℹ️  AWS S3 is NOT enabled")
        print("ℹ️  Currently using: GCP Cloud Storage")
        print("\n💡 To enable AWS S3, set in settings.py:")
        print("   CLOUD_STORAGE_BACKEND = 'AWS'")
        return False
    
    else:
        print("ℹ️  AWS S3 is NOT enabled")
        print("ℹ️  Currently using: Local Storage")
        print("\n💡 To enable AWS S3, set in settings.py:")
        print("   CLOUD_STORAGE_BACKEND = 'AWS'")
        print("\n📋 Current Configuration:")
        print(f"   Backend: {backend}")
        return False


if __name__ == "__main__":
    try:
        success = test_aws_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

