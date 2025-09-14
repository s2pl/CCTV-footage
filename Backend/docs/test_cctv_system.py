#!/usr/bin/env python3
"""
CCTV Streaming System Test Script
Tests all the major functionality of the CCTV system
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/v0/api"
CREDENTIALS = {
    "email": "admin@admin.com",
    "password": "@Rishi21"
}

class CCTVTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.cameras = []
        
    def authenticate(self):
        """Authenticate with the server and get JWT token"""
        print("🔐 Authenticating...")
        try:
            # Use the custom users login endpoint instead of DRF token endpoint
            response = self.session.post(
                f"{BASE_URL}/users/auth/login/",
                json=CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')  # Note: custom endpoint uses 'access_token'
                if not self.auth_token:
                    print("❌ No access token received in response")
                    print(f"Response data: {data}")
                    return False
                
                # Set the token in session headers for all subsequent requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                print("✅ Authentication successful!")
                print(f"   Token: {self.auth_token[:50]}...")
                print(f"   User: {data.get('user', {}).get('email', 'Unknown')}")
                print(f"   Role: {data.get('user', {}).get('role', 'Unknown')}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_multi_stream_dashboard(self):
        """Test the multi-stream dashboard endpoint"""
        print("\n📊 Testing Multi-Stream Dashboard...")
        try:
            # Make sure we have the auth token in headers
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            print(f"   Using token: {self.auth_token[:30]}...")
            
            response = self.session.get(f"{BASE_URL}/cctv/cameras/multi-stream/")
            
            if response.status_code == 200:
                data = response.json()
                self.cameras = data.get('cameras', [])
                print(f"✅ Dashboard loaded successfully!")
                print(f"   Total cameras: {data.get('total_cameras', 0)}")
                print(f"   Online cameras: {data.get('online_cameras', 0)}")
                print(f"   Streaming cameras: {data.get('streaming_cameras', 0)}")
                
                for camera in self.cameras:
                    print(f"   📹 {camera.get('camera_name', 'Unknown')} - {camera.get('status', 'Unknown')}")
                
                return True
            else:
                print(f"❌ Dashboard failed: {response.status_code}")
                print(f"Response: {response.text}")
                print(f"Headers sent: {dict(self.session.headers)}")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard error: {e}")
            return False
    
    def test_camera_stream_activation(self):
        """Test activating a camera stream"""
        if not self.cameras:
            print("⚠️  No cameras available for testing")
            return False
            
        print(f"\n🎬 Testing Camera Stream Activation...")
        camera = self.cameras[0]  # Use first camera
        camera_id = camera.get('camera_id')
        camera_name = camera.get('camera_name', 'Unknown')
        
        try:
            # Test main quality stream
            response = self.session.post(
                f"{BASE_URL}/cctv/cameras/{camera_id}/activate_stream/",
                params={"quality": "main"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Stream activated for {camera_name} (main quality)")
                return True
            else:
                print(f"❌ Stream activation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Stream activation error: {e}")
            return False
    
    def test_camera_stream_deactivation(self):
        """Test deactivating a camera stream"""
        if not self.cameras:
            print("⚠️  No cameras available for testing")
            return False
            
        print(f"\n⏹️  Testing Camera Stream Deactivation...")
        
        # Try to find a working test camera first
        working_camera = None
        for camera in self.cameras:
            if "Working Test Camera" in camera.get('camera_name', ''):
                working_camera = camera
                break
        
        # If no working test camera, use the first available
        if not working_camera:
            working_camera = self.cameras[0]
            
        camera_id = working_camera.get('camera_id')
        camera_name = working_camera.get('camera_name', 'Unknown')
        
        try:
            response = self.session.post(
                f"{BASE_URL}/cctv/cameras/{camera_id}/deactivate_stream/"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Stream deactivated for {camera_name}")
                return True
            else:
                print(f"❌ Stream deactivation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Stream deactivation error: {e}")
            return False
    
    def test_snapshot_capture(self):
        """Test capturing a snapshot"""
        if not self.cameras:
            print("⚠️  No cameras available for testing")
            return False
            
        print(f"\n📸 Testing Snapshot Capture...")
        
        # Try to find a working test camera first
        working_camera = None
        for camera in self.cameras:
            if "Working Test Camera" in camera.get('camera_name', ''):
                working_camera = camera
                break
        
        # If no working test camera, use the first available
        if not working_camera:
            working_camera = self.cameras[0]
            
        camera_id = working_camera.get('camera_id')
        camera_name = working_camera.get('camera_name', 'Unknown')
        
        try:
            response = self.session.get(
                f"{BASE_URL}/cctv/cameras/{camera_id}/stream/snapshot/",
                params={"quality": "main"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Snapshot captured for {camera_name}")
                print(f"   Filename: {data.get('snapshot', {}).get('filename', 'Unknown')}")
                return True
            else:
                print(f"❌ Snapshot capture failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Snapshot capture error: {e}")
            return False
    
    def test_thumbnail_generation(self):
        """Test thumbnail generation"""
        if not self.cameras:
            print("⚠️  No cameras available for testing")
            return False
            
        print(f"\n🖼️  Testing Thumbnail Generation...")
        
        # Try to find a working test camera first
        working_camera = None
        for camera in self.cameras:
            if "Working Test Camera" in camera.get('camera_name', ''):
                working_camera = camera
                break
        
        # If no working test camera, use the first available
        if not working_camera:
            working_camera = self.cameras[0]
            
        camera_id = working_camera.get('camera_id')
        camera_name = working_camera.get('camera_name', 'Unknown')
        
        try:
            response = self.session.get(
                f"{BASE_URL}/cctv/cameras/{camera_id}/stream/thumbnail/",
                params={"quality": "main"}
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    print(f"✅ Thumbnail generated for {camera_name}")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Size: {len(response.content)} bytes")
                    return True
                else:
                    print(f"⚠️  Thumbnail response is not an image: {content_type}")
                    return False
            else:
                print(f"❌ Thumbnail generation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Thumbnail generation error: {e}")
            return False
    
    def test_connection_test(self):
        """Test camera connection testing"""
        if not self.cameras:
            print("⚠️  No cameras available for testing")
            return False
            
        print(f"\n🔌 Testing Connection Test...")
        
        # Try to find a working test camera first
        working_camera = None
        for camera in self.cameras:
            if "Working Test Camera" in camera.get('camera_name', ''):
                working_camera = camera
                break
        
        # If no working test camera, use the first available
        if not working_camera:
            working_camera = self.cameras[0]
            
        camera_id = working_camera.get('camera_id')
        camera_name = working_camera.get('camera_name', 'Unknown')
        
        try:
            response = self.session.post(
                f"{BASE_URL}/cctv/cameras/{camera_id}/test_connection/"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connection test completed for {camera_name}")
                print(f"   Message: {data.get('message', 'No message')}")
                return True
            else:
                print(f"❌ Connection test failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Connection test error: {e}")
            return False
    
    def test_stream_health(self):
        """Test stream health endpoint"""
        if not self.cameras:
            print("⚠️  No cameras available for testing")
            return False
            
        print(f"\n💓 Testing Stream Health...")
        
        # Try to find a working test camera first
        working_camera = None
        for camera in self.cameras:
            if "Working Test Camera" in camera.get('camera_name', ''):
                working_camera = camera
                break
        
        # If no working test camera, use the first available
        if not working_camera:
            working_camera = self.cameras[0]
            
        camera_id = working_camera.get('camera_id')
        camera_name = working_camera.get('camera_name', 'Unknown')
        
        try:
            response = self.session.get(
                f"{BASE_URL}/cctv/cameras/{camera_id}/stream_health/"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Stream health check completed for {camera_name}")
                print(f"   Status: {data.get('status', 'Unknown')}")
                print(f"   Error: {data.get('error', 'None')}")
                return True
            else:
                print(f"❌ Stream health check failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Stream health check error: {e}")
            return False
    
    def test_openapi_docs(self):
        """Test OpenAPI documentation endpoint"""
        print(f"\n📚 Testing OpenAPI Documentation...")
        try:
            # Try the Django Ninja OpenAPI endpoint
            response = self.session.get(f"{BASE_URL}/cctv/openapi.json")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ OpenAPI documentation loaded successfully!")
                print(f"   Title: {data.get('info', {}).get('title', 'Unknown')}")
                print(f"   Version: {data.get('info', {}).get('version', 'Unknown')}")
                print(f"   Endpoints: {len(data.get('paths', {}))}")
                return True
            else:
                print(f"❌ OpenAPI documentation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAPI documentation error: {e}")
            return False
    
    def test_health_check(self):
        """Test the health check endpoint"""
        print(f"\n💚 Testing Health Check...")
        try:
            response = self.session.get(f"{BASE_URL}/cctv/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check successful!")
                print(f"   Status: {data.get('status', 'Unknown')}")
                print(f"   Service: {data.get('service', 'Unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting CCTV System Tests...")
        print(f"📍 Server: {BASE_URL}")
        print(f"👤 User: {CREDENTIALS['email']}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Test authentication first
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Run all tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Multi-Stream Dashboard", self.test_multi_stream_dashboard),
            ("OpenAPI Documentation", self.test_openapi_docs),
            ("Stream Health Check", self.test_stream_health),
            ("Connection Test", self.test_connection_test),
            ("Stream Activation", self.test_camera_stream_activation),
            ("Thumbnail Generation", self.test_thumbnail_generation),
            ("Snapshot Capture", self.test_snapshot_capture),
            ("Stream Deactivation", self.test_camera_stream_deactivation),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                results.append((test_name, False))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 Test Results Summary:")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print("=" * 60)
        print(f"🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! The CCTV system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        return passed == total

def main():
    """Main function"""
    tester = CCTVTester()
    
    try:
        success = tester.run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
