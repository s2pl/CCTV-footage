#!/usr/bin/env python
"""
Cleanup Failed Recordings Script
This script helps clean up database entries for recordings that have missing or invalid files.
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
from django.conf import settings

def main():
    print("🧹 Cleanup Failed Recordings Script")
    print("=" * 50)
    
    # Find recordings with missing files
    recordings = Recording.objects.filter(storage_type='local')
    missing_files = []
    tmp_files = []
    valid_files = []
    
    print("🔍 Scanning recordings for file issues...")
    
    for recording in recordings:
        if not recording.file_path:
            missing_files.append(recording)
            continue
            
        local_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, recording.file_path))
        
        if recording.file_path.endswith('.tmp'):
            tmp_files.append(recording)
        elif not os.path.exists(local_path):
            missing_files.append(recording)
        else:
            valid_files.append(recording)
    
    print(f"\n📊 Scan Results:")
    print(f"   Valid files: {len(valid_files)}")
    print(f"   Missing files: {len(missing_files)}")
    print(f"   .tmp files: {len(tmp_files)}")
    
    # Show details for problematic recordings
    if missing_files:
        print(f"\n❌ Recordings with missing files ({len(missing_files)}):")
        for recording in missing_files[:10]:  # Show first 10
            print(f"   • {recording.name} - {recording.camera.name} - {recording.start_time}")
            print(f"     File: {recording.file_path}")
        if len(missing_files) > 10:
            print(f"   ... and {len(missing_files) - 10} more")
    
    if tmp_files:
        print(f"\n⚠️  Recordings with .tmp files ({len(tmp_files)}):")
        for recording in tmp_files[:10]:  # Show first 10
            print(f"   • {recording.name} - {recording.camera.name} - {recording.start_time}")
            print(f"     File: {recording.file_path}")
        if len(tmp_files) > 10:
            print(f"   ... and {len(tmp_files) - 10} more")
    
    # Options for cleanup
    if missing_files or tmp_files:
        print(f"\n🛠️  Cleanup Options:")
        print(f"   1. Delete recordings with missing files ({len(missing_files)} recordings)")
        print(f"   2. Delete recordings with .tmp files ({len(tmp_files)} recordings)")
        print(f"   3. Delete both missing and .tmp file recordings ({len(missing_files) + len(tmp_files)} recordings)")
        print(f"   4. Just show the list and exit")
        
        choice = input("\nSelect option (1-4) or 'q' to quit: ").strip()
        
        if choice == '1':
            cleanup_recordings(missing_files, "missing files")
        elif choice == '2':
            cleanup_recordings(tmp_files, ".tmp files")
        elif choice == '3':
            cleanup_recordings(missing_files + tmp_files, "missing and .tmp files")
        elif choice == '4':
            print("📋 List displayed. No cleanup performed.")
        else:
            print("❌ Invalid choice or cancelled.")
    else:
        print("\n✅ No problematic recordings found!")

def cleanup_recordings(recordings, description):
    """Delete the specified recordings from database"""
    if not recordings:
        return
    
    print(f"\n⚠️  About to delete {len(recordings)} recordings with {description}")
    print("This action cannot be undone!")
    
    confirm = input("Type 'DELETE' to confirm: ").strip()
    if confirm != 'DELETE':
        print("❌ Deletion cancelled.")
        return
    
    deleted_count = 0
    for recording in recordings:
        try:
            recording.delete()
            deleted_count += 1
            print(f"   🗑️  Deleted: {recording.name} - {recording.camera.name}")
        except Exception as e:
            print(f"   ❌ Failed to delete {recording.name}: {str(e)}")
    
    print(f"\n✅ Successfully deleted {deleted_count} recordings")

if __name__ == '__main__':
    main()
