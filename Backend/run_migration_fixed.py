#!/usr/bin/env python
"""
Fixed GCP Migration Script
This script runs the migration with proper error handling and fixes for the issues you encountered.
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

from django.core.management import call_command
from apps.cctv.models import Recording
from django.conf import settings

def main():
    print("🚀 Running Fixed GCP Migration Script")
    print("=" * 60)
    
    # Check GCP configuration
    print("📋 Checking GCP Configuration...")
    print(f"   Bucket: {settings.GCP_STORAGE_BUCKET_NAME}")
    print(f"   Project: {settings.GCP_STORAGE_PROJECT_ID}")
    print(f"   Credentials: {settings.GCP_STORAGE_CREDENTIALS_PATH}")
    print(f"   GCP Enabled: {settings.GCP_STORAGE_USE_GCS}")
    
    if not settings.GCP_STORAGE_USE_GCS:
        print("❌ GCP Storage is not enabled. Please set GCP_STORAGE_USE_GCS=True in settings.py")
        return
    
    # Check credentials file
    credentials_path = os.path.join(BASE_DIR, settings.GCP_STORAGE_CREDENTIALS_PATH)
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        return
    
    print("✅ GCP Configuration looks good!\n")
    
    # Show current recordings status
    print("📊 Current Recordings Status:")
    total_recordings = Recording.objects.count()
    local_recordings = Recording.objects.filter(storage_type='local').count()
    gcp_recordings = Recording.objects.filter(storage_type='gcp').count()
    
    print(f"   Total recordings: {total_recordings}")
    print(f"   Local storage: {local_recordings}")
    print(f"   GCP storage: {gcp_recordings}")
    
    if local_recordings == 0:
        print("✅ No recordings need migration!")
        return
    
    print(f"\n📦 Found {local_recordings} recordings to migrate")
    
    # Skip dry run and proceed directly with migration
    print("\n🚀 Starting direct migration to GCP with fixes...")
    try:
        call_command(
            'migrate_to_gcp',
            '--batch-size=3',  # Smaller batches to avoid timeouts
            '--skip-missing',  # Skip missing files instead of failing
            '--cleanup-tmp',   # Clean up .tmp files
        )
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return
    
    # Final status
    print("\n📊 Final Status:")
    local_recordings_after = Recording.objects.filter(storage_type='local').count()
    gcp_recordings_after = Recording.objects.filter(storage_type='gcp').count()
    
    print(f"   Local storage: {local_recordings_after}")
    print(f"   GCP storage: {gcp_recordings_after}")
    
    migrated = gcp_recordings_after - gcp_recordings
    print(f"   Successfully migrated: {migrated} recordings")
    
    if local_recordings_after > 0:
        print(f"\n⚠️  {local_recordings_after} recordings still in local storage.")
        print("   These might be missing files or failed uploads.")
        print("   Check the logs above for details.")
    else:
        print("\n🎉 All recordings successfully migrated to GCP!")

if __name__ == '__main__':
    main()
