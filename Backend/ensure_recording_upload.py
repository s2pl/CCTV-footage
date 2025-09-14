#!/usr/bin/env python
"""
Script to ensure all completed recordings are uploaded to GCP
Run this periodically or after recording sessions to ensure no uploads are missed
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

from apps.cctv.models import Recording
from apps.cctv.storage_service import storage_service
from django.conf import settings
import time


def ensure_all_recordings_uploaded():
    """Ensure all completed recordings are uploaded to GCP"""
    
    print("🔄 Checking for recordings that need GCP upload...")
    
    # Get completed recordings that are still in local storage
    local_recordings = Recording.objects.filter(
        status='completed',
        storage_type='local'
    ).exclude(file_path='').exclude(file_path__endswith='.tmp')
    
    if not local_recordings.exists():
        print("✅ All recordings are already uploaded to GCP!")
        return
    
    print(f"📊 Found {local_recordings.count()} recordings to upload")
    
    # Check GCP configuration
    if not getattr(settings, 'GCP_STORAGE_USE_GCS', False):
        print("❌ GCP storage is not enabled in settings")
        return
    
    if not storage_service.use_gcp:
        print("❌ GCP storage service is not available")
        return
    
    uploaded_count = 0
    failed_count = 0
    
    for recording in local_recordings:
        try:
            print(f"\n📹 Processing: {recording.name}")
            print(f"   Camera: {recording.camera.name}")
            print(f"   Created: {recording.created_at}")
            print(f"   Size: {recording.file_size_mb} MB")
            
            # Check if local file exists
            local_file_path = os.path.join(settings.MEDIA_ROOT, recording.file_path)
            
            if not os.path.exists(local_file_path):
                print(f"   ⚠️  Local file not found: {local_file_path}")
                failed_count += 1
                continue
            
            # Upload to GCP
            print("   🚀 Uploading to GCP...")
            
            storage_result = storage_service.upload_recording(
                local_file_path=local_file_path,
                recording_id=str(recording.id),
                camera_id=str(recording.camera.id),
                filename=os.path.basename(local_file_path)
            )
            
            if storage_result[0]:  # storage_path is not None
                storage_path, storage_type = storage_result
                
                # Update recording
                recording.file_path = storage_path
                recording.storage_type = storage_type
                recording.save(update_fields=['file_path', 'storage_type'])
                
                print(f"   ✅ Successfully uploaded: {storage_path}")
                uploaded_count += 1
                
                # Clean up local file if enabled
                if getattr(settings, 'GCP_STORAGE_CLEANUP_LOCAL', True):
                    try:
                        time.sleep(2)  # Wait for GCP to process
                        os.remove(local_file_path)
                        print("   🗑️  Local file cleaned up")
                    except Exception as cleanup_error:
                        print(f"   ⚠️  Cleanup failed: {str(cleanup_error)}")
            else:
                print("   ❌ Upload failed")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed_count += 1
    
    # Summary
    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Successfully uploaded: {uploaded_count}")
    print(f"   ❌ Failed: {failed_count}")
    
    if uploaded_count > 0:
        print(f"\n🎉 {uploaded_count} recordings are now available in GCP!")
    
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} recordings still need attention")


def check_recent_recordings():
    """Check if recent recordings are being uploaded automatically"""
    from datetime import timedelta
    from django.utils import timezone
    
    print("\n🕒 Checking recent recording upload status...")
    
    # Get recordings from last 24 hours
    recent_recordings = Recording.objects.filter(
        status='completed',
        created_at__gte=timezone.now() - timedelta(hours=24)
    )
    
    if not recent_recordings.exists():
        print("   ℹ️  No recent recordings found")
        return
    
    gcp_count = recent_recordings.filter(storage_type='gcp').count()
    local_count = recent_recordings.filter(storage_type='local').count()
    total = recent_recordings.count()
    
    print(f"   📊 Recent recordings (last 24h): {total}")
    print(f"   ☁️  In GCP: {gcp_count}")
    print(f"   📁 In Local: {local_count}")
    
    if local_count == 0:
        print("   ✅ All recent recordings are in GCP - automatic upload is working!")
    else:
        print(f"   ⚠️  {local_count} recent recordings are still local - may need manual upload")
        
        # Show the local recordings
        local_recordings = recent_recordings.filter(storage_type='local')
        for recording in local_recordings[:5]:  # Show first 5
            print(f"      • {recording.name} - {recording.camera.name} - {recording.created_at}")


def main():
    print("🚀 Recording Upload Checker")
    print("=" * 50)
    
    try:
        # Check recent recordings first
        check_recent_recordings()
        
        # Ensure all recordings are uploaded
        ensure_all_recordings_uploaded()
        
        print("\n" + "=" * 50)
        print("✅ Upload check completed!")
        
    except Exception as e:
        print(f"\n❌ Error during upload check: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
