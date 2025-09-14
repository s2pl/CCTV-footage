#!/usr/bin/env python3
"""
Add Test Camera to Database
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cctv.models import Camera
from django.contrib.auth import get_user_model

User = get_user_model()

def add_test_camera():
    """Add a test camera to the database"""
    print("📹 Adding Test Camera...")
    
    try:
        # Check if test camera already exists
        existing_camera = Camera.objects.filter(name="Test Camera").first()
        if existing_camera:
            print(f"✅ Test camera already exists: {existing_camera.name}")
            print(f"   ID: {existing_camera.id}")
            print(f"   Status: {existing_camera.status}")
            return existing_camera
        
        # Create test camera
        camera = Camera.objects.create(
            name="Test Camera",
            description="Test camera for streaming system",
            ip_address="192.168.1.100",
            port=554,
            username="admin",
            password="admin123",
            rtsp_url="rtsp://admin:admin123@192.168.1.100:554/stream1",
            rtsp_url_sub="rtsp://admin:admin123@192.168.1.100:554/stream2",
            rtsp_path="/stream1",
            camera_type="rtsp",
            location="Test Location",
            is_active=True,
            status="active",
            auto_record=False,
            record_quality="medium",
            max_recording_hours=24,
            is_public=True
        )
        
        print(f"✅ Test camera created successfully!")
        print(f"   ID: {camera.id}")
        print(f"   Name: {camera.name}")
        print(f"   Status: {camera.status}")
        print(f"   RTSP URL: {camera.rtsp_url}")
        print(f"   Location: {camera.location}")
        
        return camera
        
    except Exception as e:
        print(f"❌ Error creating test camera: {e}")
        return None

def add_working_test_camera():
    """Add a test camera with a working RTSP URL for testing"""
    print("\n📹 Adding Working Test Camera...")
    
    try:
        # Check if working test camera already exists
        existing_camera = Camera.objects.filter(name="Working Test Camera").first()
        if existing_camera:
            print(f"✅ Working test camera already exists: {existing_camera.name}")
            print(f"   ID: {existing_camera.id}")
            print(f"   Status: {existing_camera.status}")
            return existing_camera
        
        # Create working test camera with a public test stream
        camera = Camera.objects.create(
            name="Working Test Camera",
            description="Test camera with working RTSP stream for testing",
            ip_address="127.0.0.1",
            port=554,
            username="",
            password="",
            # Use a public test RTSP stream that should be accessible
            rtsp_url="rtsp://demo:demo@ipvmdemo.dyndns.org:5541/onvif-media/media.amp",
            rtsp_url_sub="rtsp://demo:demo@ipvmdemo.dyndns.org:5541/onvif-media/media.amp",
            rtsp_path="/onvif-media/media.amp",
            camera_type="rtsp",
            location="Test Lab",
            is_active=True,
            status="active",
            auto_record=False,
            record_quality="medium",
            max_recording_hours=24,
            is_public=True
        )
        
        print(f"✅ Working test camera created successfully!")
        print(f"   ID: {camera.id}")
        print(f"   Name: {camera.name}")
        print(f"   Status: {camera.status}")
        print(f"   RTSP URL: {camera.rtsp_url}")
        print(f"   Location: {camera.location}")
        
        return camera
        
    except Exception as e:
        print(f"❌ Error creating working test camera: {e}")
        return None

def add_sample_cameras():
    """Add multiple sample cameras for testing"""
    print("\n📹 Adding Sample Cameras...")
    
    sample_cameras = [
        {
            "name": "Front Door Camera",
            "description": "Main entrance surveillance",
            "ip_address": "192.168.1.101",
            "rtsp_url": "rtsp://admin:admin123@192.168.1.101:554/stream1",
            "rtsp_url_sub": "rtsp://admin:admin123@192.168.1.101:554/stream2",
            "location": "Front Entrance",
        },
        {
            "name": "Backyard Camera",
            "description": "Backyard monitoring",
            "ip_address": "192.168.1.102",
            "rtsp_url": "rtsp://admin:admin123@192.168.1.102:554/stream1",
            "rtsp_url_sub": "rtsp://admin:admin123@192.168.1.102:554/stream2",
            "location": "Backyard",
        },
        {
            "name": "Parking Lot Camera",
            "description": "Parking area surveillance",
            "ip_address": "192.168.1.103",
            "rtsp_url": "rtsp://admin:admin123@192.168.1.103:554/stream1",
            "rtsp_url_sub": "rtsp://admin:admin123@192.168.1.103:554/stream2",
            "location": "Parking Lot",
        }
    ]
    
    created_cameras = []
    
    for camera_data in sample_cameras:
        try:
            # Check if camera already exists
            existing = Camera.objects.filter(name=camera_data["name"]).first()
            if existing:
                print(f"   ⚠️  Camera '{camera_data['name']}' already exists")
                created_cameras.append(existing)
                continue
            
            # Create camera
            camera = Camera.objects.create(
                name=camera_data["name"],
                description=camera_data["description"],
                ip_address=camera_data["ip_address"],
                port=554,
                username="admin",
                password="admin123",
                rtsp_url=camera_data["rtsp_url"],
                rtsp_url_sub=camera_data["rtsp_url_sub"],
                rtsp_path="/stream1",
                camera_type="rtsp",
                location=camera_data["location"],
                is_active=True,
                status="active",
                auto_record=False,
                record_quality="medium",
                max_recording_hours=24,
                is_public=True
            )
            
            print(f"   ✅ Created: {camera.name} at {camera.location}")
            created_cameras.append(camera)
            
        except Exception as e:
            print(f"   ❌ Error creating {camera_data['name']}: {e}")
    
    return created_cameras

def list_cameras():
    """List all cameras in the database"""
    print("\n📋 Current Cameras in Database:")
    print("=" * 50)
    
    cameras = Camera.objects.all()
    
    if not cameras:
        print("   No cameras found")
        return
    
    for camera in cameras:
        print(f"   📹 {camera.name}")
        print(f"      ID: {camera.id}")
        print(f"      Status: {camera.status}")
        print(f"      Location: {camera.location}")
        print(f"      RTSP: {camera.rtsp_url}")
        print(f"      Active: {camera.is_active}")
        print()

def main():
    """Main function"""
    print("🚀 CCTV Camera Setup Script")
    print("=" * 50)
    
    # Add test camera
    test_camera = add_test_camera()
    
    # Add working test camera
    working_test_camera = add_working_test_camera()
    
    # Add sample cameras
    sample_cameras = add_sample_cameras()
    
    # List all cameras
    list_cameras()
    
    print("🎉 Camera setup complete!")
    print(f"   Total cameras: {Camera.objects.count()}")
    print("\n💡 You can now run the CCTV tests:")
    print("   python test_cctv_system.py")

if __name__ == "__main__":
    main()
