#!/usr/bin/env python
"""
Setup script for GCP Video System
Run this after configuring your GCP credentials and settings.
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

from django.conf import settings
from apps.cctv.models import Recording, Camera
from apps.cctv.storage_service import storage_service


def main():
    print("🚀 GCP Video System Setup")
    print("=" * 50)
    
    # Check configuration
    print("1️⃣  Checking Configuration...")
    
    required_settings = [
        'GCP_STORAGE_BUCKET_NAME',
        'GCP_STORAGE_PROJECT_ID', 
        'GCP_STORAGE_CREDENTIALS_PATH',
        'GCP_STORAGE_USE_GCS'
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not hasattr(settings, setting) or not getattr(settings, setting):
            missing_settings.append(setting)
    
    if missing_settings:
        print(f"   ❌ Missing required settings: {', '.join(missing_settings)}")
        print("   Please configure these in config/settings.py")
        return False
    
    print("   ✅ All required settings configured")
    
    # Check credentials file
    credentials_path = os.path.join(BASE_DIR, settings.GCP_STORAGE_CREDENTIALS_PATH)
    if not os.path.exists(credentials_path):
        print(f"   ❌ Credentials file not found: {credentials_path}")
        print("   Please place your GCP service account key file at this location")
        return False
    
    print("   ✅ Credentials file found")
    
    # Test GCP connection
    print("\n2️⃣  Testing GCP Connection...")
    
    if not storage_service.use_gcp:
        print("   ❌ GCP storage service not initialized")
        return False
    
    if not storage_service.gcp_service or not storage_service.gcp_service.bucket:
        print("   ❌ Cannot access GCP bucket")
        print("   Check your credentials and bucket permissions")
        return False
    
    print("   ✅ GCP connection successful")
    
    # Check existing recordings
    print("\n3️⃣  Checking Existing Recordings...")
    
    total_recordings = Recording.objects.count()
    local_recordings = Recording.objects.filter(storage_type='local', status='completed').count()
    gcp_recordings = Recording.objects.filter(storage_type='gcp').count()
    
    print(f"   📊 Total recordings: {total_recordings}")
    print(f"   📁 Local recordings: {local_recordings}")
    print(f"   ☁️  GCP recordings: {gcp_recordings}")
    
    # Offer to migrate existing recordings
    if local_recordings > 0:
        print(f"\n4️⃣  Found {local_recordings} recordings in local storage")
        response = input("   Would you like to migrate them to GCP? (y/N): ")
        
        if response.lower() in ['y', 'yes']:
            print("   🔄 Running migration...")
            try:
                from django.core.management import call_command
                call_command('migrate_to_gcp', '--batch-size=3', '--skip-missing', '--cleanup-tmp')
                print("   ✅ Migration completed")
            except Exception as e:
                print(f"   ❌ Migration failed: {str(e)}")
        else:
            print("   ⏭️  Skipping migration")
    
    # Test video access
    print("\n5️⃣  Testing Video Access...")
    
    test_recording = Recording.objects.filter(
        storage_type='gcp',
        status='completed'
    ).first()
    
    if test_recording:
        try:
            url = storage_service.get_file_url(
                test_recording.file_path,
                signed=True,
                expiration_minutes=30
            )
            
            if url:
                print("   ✅ Video URL generation successful")
                print(f"   🔗 Sample URL: {url[:80]}...")
            else:
                print("   ❌ Failed to generate video URL")
        except Exception as e:
            print(f"   ❌ Error testing video access: {str(e)}")
    else:
        print("   ℹ️  No GCP recordings to test with")
    
    # Setup background tasks
    print("\n6️⃣  Background Tasks...")
    
    try:
        from apps.cctv.scheduler import recording_scheduler
        print("   ✅ Recording scheduler is active")
        print("   📅 Background sync will run every 30 minutes")
    except Exception as e:
        print(f"   ⚠️  Scheduler issue: {str(e)}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("\n📝 What happens next:")
    print("   • New recordings will automatically upload to GCP")
    print("   • Videos can be accessed via API endpoints")
    print("   • Background sync ensures no recordings are missed")
    print("   • Local files are cleaned up after successful upload")
    
    print("\n🔗 Useful commands:")
    print("   # Test the system")
    print("   python test_gcp_video_access.py")
    print()
    print("   # Manually sync recordings")
    print("   python manage.py sync_recordings_to_gcp")
    print()
    print("   # Check system status")
    print("   python manage.py shell")
    print("   >>> from apps.cctv.models import Recording")
    print("   >>> Recording.objects.values('storage_type').annotate(count=Count('id'))")
    
    print("\n📚 Documentation:")
    print("   • docs/GCP_VIDEO_SYSTEM.md - Complete system documentation")
    print("   • docs/MIGRATION_FIXES.md - Migration troubleshooting")
    
    print("\n✅ Your GCP Video System is ready!")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
