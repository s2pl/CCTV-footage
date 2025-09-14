"""
Management command to test the connection between users and CCTV apps
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection
from django.apps import apps
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Test the connection between users and CCTV apps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('🔍 Testing Users and CCTV App Connection...'))
        self.stdout.write('=' * 60)
        
        # Test 1: Check if apps are installed
        self.test_app_installation()
        
        # Test 2: Check database connections
        self.test_database_connections()
        
        # Test 3: Check permission system
        self.test_permission_system()
        
        # Test 4: Check model relationships
        self.test_model_relationships()
        
        # Test 5: Check API endpoints
        self.test_api_endpoints()
        
        self.stdout.write(self.style.SUCCESS('✅ App connection test completed!'))

    def test_app_installation(self):
        """Test if both apps are properly installed"""
        self.stdout.write('\n📱 Testing App Installation...')
        
        try:
            users_app = apps.get_app_config('users')
            cctv_app = apps.get_app_config('cctv')
            
            self.stdout.write(f"✅ Users app: {users_app.name} ({users_app.verbose_name})")
            self.stdout.write(f"✅ CCTV app: {cctv_app.name} ({cctv_app.verbose_name})")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ App installation test failed: {e}"))

    def test_database_connections(self):
        """Test database connections for both apps"""
        self.stdout.write('\n🗄️ Testing Database Connections...')
        
        try:
            with connection.cursor() as cursor:
                # Test users table
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                self.stdout.write(f"✅ Users table accessible: {user_count} users found")
                
                # Test CCTV tables
                cursor.execute("SELECT COUNT(*) FROM cctv_camera")
                camera_count = cursor.fetchone()[0]
                self.stdout.write(f"✅ Cameras table accessible: {camera_count} cameras found")
                
                cursor.execute("SELECT COUNT(*) FROM cctv_cameraaccess")
                access_count = cursor.fetchone()[0]
                self.stdout.write(f"✅ Camera access table accessible: {access_count} access records found")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Database connection test failed: {e}"))

    def test_permission_system(self):
        """Test the permission system integration"""
        self.stdout.write('\n🔐 Testing Permission System...')
        
        try:
            from apps.users.permissions import RoleBasedPermission
            
            # Test with a superuser
            superuser = User.objects.filter(is_superuser=True).first()
            if superuser:
                role = RoleBasedPermission.get_user_role(superuser)
                can_access_cctv = RoleBasedPermission.can_access_app(superuser, 'cctv')
                can_manage_cameras = RoleBasedPermission.can_perform_action(superuser, 'cctv', 'manage_cameras')
                
                self.stdout.write(f"✅ Permission system working for superuser: {superuser.username}")
                self.stdout.write(f"   Role: {role}")
                self.stdout.write(f"   CCTV Access: {can_access_cctv}")
                self.stdout.write(f"   Can Manage Cameras: {can_manage_cameras}")
            else:
                self.stdout.write(self.style.WARNING("⚠️ No superuser found for permission testing"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Permission system test failed: {e}"))

    def test_model_relationships(self):
        """Test model relationships between apps"""
        self.stdout.write('\n🔗 Testing Model Relationships...')
        
        try:
            from apps.cctv.models import Camera, CameraAccess
            
            # Test user relationship in Camera model
            if hasattr(Camera, 'created_by'):
                self.stdout.write("✅ Camera model has created_by field")
                
                # Test if we can create a camera with a user
                test_user = User.objects.filter(is_superuser=True).first()
                if test_user:
                    try:
                        # Just test the relationship, don't save
                        camera = Camera(
                            name="Test Camera",
                            ip_address="192.168.1.100",
                            rtsp_url="rtsp://192.168.1.100:554/stream1",
                            created_by=test_user
                        )
                        self.stdout.write("✅ Camera-User relationship working correctly")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Camera-User relationship failed: {e}"))
                else:
                    self.stdout.write(self.style.WARNING("⚠️ No test user found for relationship testing"))
            else:
                self.stdout.write(self.style.ERROR("❌ Camera model missing created_by field"))
            
            # Test user relationship in CameraAccess model
            if hasattr(CameraAccess, 'user'):
                self.stdout.write("✅ CameraAccess model has user field")
            else:
                self.stdout.write(self.style.ERROR("❌ CameraAccess model missing user field"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Model relationship test failed: {e}"))

    def test_api_endpoints(self):
        """Test API endpoint availability"""
        self.stdout.write('\n🌐 Testing API Endpoints...')
        
        try:
            from apps.cctv.api import api
            from apps.users.api import api as users_api
            
            if hasattr(api, 'urls'):
                self.stdout.write("✅ CCTV API endpoints available")
            else:
                self.stdout.write(self.style.ERROR("❌ CCTV API endpoints not available"))
                
            if hasattr(users_api, 'urls'):
                self.stdout.write("✅ Users API endpoints available")
            else:
                self.stdout.write(self.style.ERROR("❌ Users API endpoints not available"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ API endpoint test failed: {e}"))
