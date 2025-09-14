#!/usr/bin/env python3
"""
Check Cameras in Database and API
"""

import os
import sys
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cctv.models import Camera

def check_database_cameras():
    """Check cameras in the database"""
    print("📋 Cameras in Database:")
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

def check_api_dashboard():
    """Check what the API dashboard returns"""
    print("\n🌐 API Dashboard Response:")
    print("=" * 50)
    
    try:
        # First get a token
        response = requests.post(
            "http://localhost:8000/v0/api/users/auth/login/",
            json={"email": "admin@admin.com", "password": "@Rishi21"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            
            if token:
                print("✅ Got authentication token")
                
                # Test dashboard endpoint
                headers = {'Authorization': f'Bearer {token}'}
                dashboard_response = requests.get(
                    "http://localhost:8000/v0/api/cctv/cameras/multi-stream/",
                    headers=headers
                )
                
                if dashboard_response.status_code == 200:
                    dashboard_data = dashboard_response.json()
                    print(f"✅ Dashboard loaded successfully!")
                    print(f"   Total cameras: {dashboard_data.get('total_cameras', 0)}")
                    print(f"   Online cameras: {dashboard_data.get('online_cameras', 0)}")
                    print(f"   Streaming cameras: {dashboard_data.get('streaming_cameras', 0)}")
                    
                    cameras = dashboard_data.get('cameras', [])
                    print(f"\n   Cameras from API:")
                    for camera in cameras:
                        print(f"      📹 {camera.get('camera_name', 'Unknown')} - {camera.get('status', 'Unknown')}")
                        print(f"         RTSP: {camera.get('rtsp_url', 'Unknown')}")
                else:
                    print(f"❌ Dashboard failed: {dashboard_response.status_code}")
                    print(f"Response: {dashboard_response.text}")
            else:
                print("❌ No access token received")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

def main():
    """Main function"""
    print("🔍 Camera System Check")
    print("=" * 50)
    
    check_database_cameras()
    check_api_dashboard()

if __name__ == "__main__":
    main()
