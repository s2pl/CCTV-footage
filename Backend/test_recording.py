#!/usr/bin/env python
"""
Test script to verify video recording functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cctv.models import Camera
from apps.cctv.streaming import recording_manager
import time

def test_recording():
    print("=== Video Recording Test ===")
    
    # Get first camera
    try:
        camera = Camera.objects.first()
        if not camera:
            print("❌ No cameras found in database")
            return False
        
        print(f"Testing recording for camera: {camera.name}")
        print(f"Camera RTSP URL: {camera.rtsp_url}")
        print(f"Camera status: {camera.status}")
        
        # Start a short recording (10 seconds)
        print("🎬 Starting 10-second test recording...")
        
        result = recording_manager.start_recording(
            camera=camera,
            duration_minutes=0.17,  # ~10 seconds
            recording_name="Test Recording - GCP Integration"
        )
        
        if result:
            recording_id, recording_name = result
            print(f"✅ Recording started successfully!")
            print(f"Recording ID: {recording_id}")
            print(f"Recording Name: {recording_name}")
            
            # Wait for recording to complete
            print("⏳ Waiting for recording to complete...")
            time.sleep(15)  # Wait a bit longer than recording duration
            
            # Check if recording file was created
            from apps.cctv.models import Recording
            try:
                recording = Recording.objects.get(id=recording_id)
                print(f"Recording file path: {recording.file_path}")
                print(f"Recording status: {recording.status}")
                print(f"Recording size: {recording.file_size_mb} MB")
                
                if recording.file_path and os.path.exists(os.path.join('media', recording.file_path)):
                    print("✅ Recording file created successfully!")
                    return True
                else:
                    print("❌ Recording file not found")
                    return False
                    
            except Recording.DoesNotExist:
                print("❌ Recording record not found in database")
                return False
        else:
            print("❌ Failed to start recording")
            return False
            
    except Exception as e:
        print(f"❌ Recording test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_recording()
    print(f"\n=== Test Result: {'PASSED' if success else 'FAILED'} ===")
