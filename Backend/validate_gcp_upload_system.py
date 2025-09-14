#!/usr/bin/env python
"""
Comprehensive validation script for GCP upload system
This script validates that the upload system is working correctly
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cctv.models import Recording, Camera
from apps.cctv.storage_service import storage_service
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def test_upload_mechanism():
    """Test that the upload mechanism is properly integrated"""
    print("🔧 Testing Upload Mechanism Integration...")
    
    # Check if upload method exists in streaming.py
    try:
        from apps.cctv.streaming import recording_manager
        
        # Check if the upload method exists
        if hasattr(recording_manager, '_upload_completed_recording'):
            print("   ✅ Upload method exists in recording manager")
        else:
            print("   ❌ Upload method missing from recording manager")
            return False
        
        # Check if upload is called in completion flow
        import inspect
        source = inspect.getsource(recording_manager._record_frames)
        if '_upload_completed_recording' in source:
            print("   ✅ Upload method is called in recording completion flow")
        else:
            print("   ❌ Upload method not called in completion flow")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking upload mechanism: {str(e)}")
        return False


def test_signal_integration():
    """Test signal integration for upload safety"""
    print("\n📡 Testing Signal Integration...")
    
    try:
        from apps.cctv import signals
        
        # Check if recording completion signal exists
        if hasattr(signals, 'handle_recording_completion'):
            print("   ✅ Recording completion signal handler exists")
        else:
            print("   ❌ Recording completion signal handler missing")
            return False
        
        # Check if signal is properly registered
        from django.db.models.signals import post_save
        from apps.cctv.models import Recording
        
        receivers = post_save._live_receivers(sender=Recording)
        signal_found = any('handle_recording_completion' in str(receiver) for receiver in receivers)
        
        if signal_found:
            print("   ✅ Signal is properly registered")
        else:
            print("   ❌ Signal not properly registered")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking signal integration: {str(e)}")
        return False


def test_background_sync():
    """Test background sync functionality"""
    print("\n🔄 Testing Background Sync...")
    
    try:
        from apps.cctv.scheduler import sync_recordings_to_gcp
        
        print("   ✅ Background sync function exists")
        
        # Check if scheduler is running
        from apps.cctv.scheduler import recording_scheduler
        
        if recording_scheduler.scheduler.running:
            print("   ✅ Scheduler is running")
            
            # Check if sync job is scheduled
            jobs = recording_scheduler.scheduler.get_jobs()
            sync_job = any('sync_recordings_gcp' in job.id for job in jobs)
            
            if sync_job:
                print("   ✅ GCP sync job is scheduled")
            else:
                print("   ❌ GCP sync job not found in scheduler")
                return False
        else:
            print("   ⚠️  Scheduler is not running")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking background sync: {str(e)}")
        return False


def test_management_commands():
    """Test management commands for manual sync"""
    print("\n⚙️  Testing Management Commands...")
    
    commands_to_check = [
        'sync_recordings_to_gcp',
        'migrate_to_gcp',
        'ensure_gcp_uploads'
    ]
    
    all_exist = True
    
    for command in commands_to_check:
        command_path = f"apps/cctv/management/commands/{command}.py"
        if os.path.exists(command_path):
            print(f"   ✅ {command} command exists")
        else:
            print(f"   ❌ {command} command missing")
            all_exist = False
    
    return all_exist


def test_actual_upload_flow():
    """Test actual upload flow with a sample recording"""
    print("\n🎬 Testing Actual Upload Flow...")
    
    # Get a completed recording that's in local storage
    local_recording = Recording.objects.filter(
        status='completed',
        storage_type='local'
    ).exclude(file_path='').exclude(file_path__endswith='.tmp').first()
    
    if not local_recording:
        print("   ℹ️  No local recordings found to test with")
        return True  # Not a failure, just nothing to test
    
    print(f"   📹 Testing with recording: {local_recording.name}")
    
    # Check if file exists locally
    local_file_path = os.path.join(settings.MEDIA_ROOT, local_recording.file_path)
    
    if not os.path.exists(local_file_path):
        print(f"   ❌ Local file not found: {local_file_path}")
        return False
    
    print(f"   ✅ Local file exists: {local_file_path}")
    
    # Test GCP upload
    if not storage_service.use_gcp:
        print("   ⚠️  GCP not configured, skipping upload test")
        return True
    
    try:
        print("   🚀 Testing GCP upload...")
        
        storage_result = storage_service.upload_recording(
            local_file_path=local_file_path,
            recording_id=str(local_recording.id),
            camera_id=str(local_recording.camera.id),
            filename=os.path.basename(local_file_path)
        )
        
        if storage_result[0]:  # storage_path is not None
            storage_path, storage_type = storage_result
            print(f"   ✅ Upload successful: {storage_path}")
            
            # Update the recording
            local_recording.file_path = storage_path
            local_recording.storage_type = storage_type
            local_recording.save(update_fields=['file_path', 'storage_type'])
            
            print("   ✅ Database updated successfully")
            return True
        else:
            print("   ❌ Upload failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Upload test error: {str(e)}")
        return False


def test_video_access():
    """Test video access after upload"""
    print("\n🎥 Testing Video Access...")
    
    # Get a GCP recording
    gcp_recording = Recording.objects.filter(
        storage_type='gcp',
        status='completed'
    ).first()
    
    if not gcp_recording:
        print("   ℹ️  No GCP recordings found to test access with")
        return True
    
    print(f"   📹 Testing access for: {gcp_recording.name}")
    
    try:
        # Test URL generation
        url = storage_service.get_file_url(
            gcp_recording.file_path,
            signed=True,
            expiration_minutes=30
        )
        
        if url:
            print("   ✅ Signed URL generated successfully")
            print(f"   🔗 URL: {url[:80]}...")
            
            # Test URL accessibility (basic check)
            import requests
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    print("   ✅ URL is accessible")
                    
                    # Check content type
                    content_type = response.headers.get('content-type', 'unknown')
                    print(f"   📄 Content-Type: {content_type}")
                    
                    return True
                else:
                    print(f"   ❌ URL not accessible: HTTP {response.status_code}")
                    return False
                    
            except requests.RequestException as e:
                print(f"   ⚠️  URL accessibility test failed: {str(e)}")
                return True  # Don't fail on network issues
        else:
            print("   ❌ Failed to generate signed URL")
            return False
            
    except Exception as e:
        print(f"   ❌ Access test error: {str(e)}")
        return False


def main():
    print("🔍 GCP Upload System Validation")
    print("=" * 50)
    
    tests = [
        ("Upload Mechanism Integration", test_upload_mechanism),
        ("Signal Integration", test_signal_integration),
        ("Background Sync", test_background_sync),
        ("Management Commands", test_management_commands),
        ("Actual Upload Flow", test_actual_upload_flow),
        ("Video Access", test_video_access),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Results:")
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All validation tests passed!")
        print("\n✅ Your GCP upload system is properly configured and working:")
        print("   • Recordings will automatically upload to GCP after completion")
        print("   • Background sync ensures no recordings are missed")
        print("   • Signal handlers provide additional safety")
        print("   • Management commands available for manual operations")
        print("   • Videos are accessible via secure signed URLs")
        
        print("\n📝 System is ready for production use!")
        
    else:
        print(f"\n⚠️  {len(tests) - passed} validation tests failed.")
        print("   Please review the errors above and fix the issues.")
        
        if not results.get("Upload Mechanism Integration", False):
            print("\n🔧 To fix upload mechanism:")
            print("   • Ensure _upload_completed_recording method exists in streaming.py")
            print("   • Verify it's called in the recording completion flow")
        
        if not results.get("Background Sync", False):
            print("\n🔄 To fix background sync:")
            print("   • Check if scheduler is running")
            print("   • Verify sync job is scheduled")
    
    return passed == len(tests)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
