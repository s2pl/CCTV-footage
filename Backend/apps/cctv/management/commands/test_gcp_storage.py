"""
Management command to test GCP Cloud Storage configuration and connectivity.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import tempfile
from apps.cctv.storage_service import storage_service, GCP_AVAILABLE


class Command(BaseCommand):
    help = 'Test GCP Cloud Storage configuration and connectivity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--upload-test',
            action='store_true',
            help='Upload a test file to verify write permissions',
        )
        parser.add_argument(
            '--download-test',
            action='store_true',
            help='Download a test file to verify read permissions',
        )
        parser.add_argument(
            '--list-bucket',
            action='store_true',
            help='List files in the bucket',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Testing GCP Cloud Storage Configuration...\n')
        )

        # Check if GCP is available
        if not GCP_AVAILABLE:
            self.stdout.write(
                self.style.ERROR('❌ Google Cloud Storage packages not installed!')
            )
            self.stdout.write('Install with: pip install google-cloud-storage google-cloud-core')
            return

        # Check configuration
        self.check_configuration()

        # Test storage service initialization
        self.test_storage_service()

        # Run specific tests
        if options['upload_test']:
            self.test_upload()
        
        if options['download_test']:
            self.test_download()
        
        if options['list_bucket']:
            self.test_list_bucket()

        # If no specific tests requested, run basic connectivity test
        if not any([options['upload_test'], options['download_test'], options['list_bucket']]):
            self.test_basic_connectivity()

    def check_configuration(self):
        """Check if GCP configuration is properly set"""
        self.stdout.write('📋 Checking Configuration...')
        
        config_items = [
            ('GCP_STORAGE_USE_GCS', getattr(settings, 'GCP_STORAGE_USE_GCS', False)),
            ('GCP_STORAGE_PROJECT_ID', getattr(settings, 'GCP_STORAGE_PROJECT_ID', '')),
            ('GCP_STORAGE_BUCKET_NAME', getattr(settings, 'GCP_STORAGE_BUCKET_NAME', '')),
            ('GCP_STORAGE_CREDENTIALS_PATH', getattr(settings, 'GCP_STORAGE_CREDENTIALS_PATH', '')),
        ]

        for key, value in config_items:
            if value:
                self.stdout.write(f'  ✅ {key}: {value}')
            else:
                self.stdout.write(f'  ⚠️  {key}: Not set')

        # Check credentials file
        creds_path = getattr(settings, 'GCP_STORAGE_CREDENTIALS_PATH', '')
        if creds_path:
            if os.path.exists(creds_path):
                self.stdout.write(f'  ✅ Credentials file exists: {creds_path}')
            else:
                self.stdout.write(f'  ❌ Credentials file not found: {creds_path}')
        else:
            self.stdout.write('  ℹ️  Using default credentials (GOOGLE_APPLICATION_CREDENTIALS or metadata server)')

        self.stdout.write('')

    def test_storage_service(self):
        """Test storage service initialization"""
        self.stdout.write('🔧 Testing Storage Service Initialization...')
        
        try:
            if storage_service.use_gcp:
                self.stdout.write('  ✅ Using GCP Storage')
                if storage_service.gcp_service and storage_service.gcp_service.client:
                    self.stdout.write('  ✅ GCP Client initialized successfully')
                else:
                    self.stdout.write('  ❌ Failed to initialize GCP client')
                    return False
            else:
                self.stdout.write('  ℹ️  Using Local Storage')
            
            return True
        except Exception as e:
            self.stdout.write(f'  ❌ Error initializing storage service: {str(e)}')
            return False

    def test_basic_connectivity(self):
        """Test basic connectivity to GCP Storage"""
        self.stdout.write('🌐 Testing Basic Connectivity...')
        
        if not storage_service.use_gcp:
            self.stdout.write('  ℹ️  GCP Storage not enabled, skipping connectivity test')
            return

        try:
            # Test bucket access
            if storage_service.gcp_service and storage_service.gcp_service.bucket:
                self.stdout.write('  ✅ Successfully connected to GCP Storage bucket')
                self.stdout.write(f'  📦 Bucket: {storage_service.gcp_service.bucket_name}')
                self.stdout.write(f'  🏢 Project: {storage_service.gcp_service.project_id}')
            else:
                self.stdout.write('  ❌ Failed to connect to GCP Storage bucket')
                return False

            return True
        except Exception as e:
            self.stdout.write(f'  ❌ Connectivity test failed: {str(e)}')
            return False

    def test_upload(self):
        """Test file upload to GCP Storage"""
        self.stdout.write('📤 Testing File Upload...')
        
        if not storage_service.use_gcp:
            self.stdout.write('  ℹ️  GCP Storage not enabled, skipping upload test')
            return

        try:
            # Create a test file
            test_content = b'This is a test file for GCP Storage upload test.'
            test_filename = 'test-upload.txt'
            test_path = f'test/{test_filename}'
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name

            # Upload the file
            success = storage_service.gcp_service.upload_file(
                temp_file_path,
                test_path,
                content_type='text/plain'
            )

            if success:
                self.stdout.write(f'  ✅ Successfully uploaded test file: {test_path}')
                
                # Clean up temp file
                os.unlink(temp_file_path)
                
                # Test file existence
                if storage_service.gcp_service.file_exists(test_path):
                    self.stdout.write('  ✅ File exists in bucket')
                else:
                    self.stdout.write('  ❌ File not found in bucket after upload')
                
                # Clean up test file
                storage_service.gcp_service.delete_file(test_path)
                self.stdout.write('  🧹 Cleaned up test file')
            else:
                self.stdout.write('  ❌ Failed to upload test file')
                os.unlink(temp_file_path)

        except Exception as e:
            self.stdout.write(f'  ❌ Upload test failed: {str(e)}')

    def test_download(self):
        """Test file download from GCP Storage"""
        self.stdout.write('📥 Testing File Download...')
        
        if not storage_service.use_gcp:
            self.stdout.write('  ℹ️  GCP Storage not enabled, skipping download test')
            return

        try:
            # First upload a test file
            test_content = b'This is a test file for GCP Storage download test.'
            test_filename = 'test-download.txt'
            test_path = f'test/{test_filename}'
            
            # Create temporary file for upload
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name

            # Upload the file
            upload_success = storage_service.gcp_service.upload_file(
                temp_file_path,
                test_path,
                content_type='text/plain'
            )

            if not upload_success:
                self.stdout.write('  ❌ Failed to upload test file for download test')
                os.unlink(temp_file_path)
                return

            # Clean up upload temp file
            os.unlink(temp_file_path)

            # Test download
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as download_temp:
                download_success = storage_service.gcp_service.download_file(
                    test_path,
                    download_temp.name
                )

                if download_success:
                    # Verify content
                    with open(download_temp.name, 'rb') as f:
                        downloaded_content = f.read()
                    
                    if downloaded_content == test_content:
                        self.stdout.write('  ✅ Successfully downloaded and verified test file')
                    else:
                        self.stdout.write('  ❌ Downloaded file content does not match')
                    
                    # Clean up download temp file
                    os.unlink(download_temp.name)
                else:
                    self.stdout.write('  ❌ Failed to download test file')

            # Clean up test file from bucket
            storage_service.gcp_service.delete_file(test_path)
            self.stdout.write('  🧹 Cleaned up test file from bucket')

        except Exception as e:
            self.stdout.write(f'  ❌ Download test failed: {str(e)}')

    def test_list_bucket(self):
        """Test listing files in the bucket"""
        self.stdout.write('📋 Testing Bucket Listing...')
        
        if not storage_service.use_gcp:
            self.stdout.write('  ℹ️  GCP Storage not enabled, skipping bucket listing test')
            return

        try:
            # List files in the bucket
            blobs = storage_service.gcp_service.bucket.list_blobs(max_results=10)
            blob_list = list(blobs)
            
            if blob_list:
                self.stdout.write(f'  📦 Found {len(blob_list)} files in bucket:')
                for blob in blob_list:
                    self.stdout.write(f'    - {blob.name} ({blob.size} bytes)')
            else:
                self.stdout.write('  📦 Bucket is empty')
            
            self.stdout.write('  ✅ Successfully listed bucket contents')

        except Exception as e:
            self.stdout.write(f'  ❌ Bucket listing test failed: {str(e)}')

    def test_url_generation(self):
        """Test URL generation for files"""
        self.stdout.write('🔗 Testing URL Generation...')
        
        if not storage_service.use_gcp:
            self.stdout.write('  ℹ️  GCP Storage not enabled, skipping URL generation test')
            return

        try:
            # Test public URL generation
            test_path = 'test/url-test.txt'
            public_url = storage_service.gcp_service.get_file_url(test_path, signed=False)
            
            if public_url:
                self.stdout.write(f'  ✅ Generated public URL: {public_url}')
            else:
                self.stdout.write('  ❌ Failed to generate public URL')

            # Test signed URL generation
            signed_url = storage_service.gcp_service.get_file_url(test_path, signed=True)
            
            if signed_url:
                self.stdout.write(f'  ✅ Generated signed URL: {signed_url[:100]}...')
            else:
                self.stdout.write('  ❌ Failed to generate signed URL')

        except Exception as e:
            self.stdout.write(f'  ❌ URL generation test failed: {str(e)}')
