#!/usr/bin/env python3
"""
Test script for the CCTV live stream endpoint
"""

import requests
import uuid
import sys
import time

def test_stream_endpoint(base_url="http://localhost:8000", camera_id=None):
    """Test the live stream endpoint"""
    
    if not camera_id:
        print("❌ No camera ID provided. Please provide a valid camera UUID.")
        print("Usage: python test_stream_endpoint.py <camera_id>")
        return False
    
    # Validate UUID format
    try:
        uuid.UUID(camera_id)
    except ValueError:
        print(f"❌ Invalid UUID format: {camera_id}")
        return False
    
    print(f"🔍 Testing stream endpoint for camera: {camera_id}")
    print(f"🌐 Base URL: {base_url}")
    
    # Test 1: Check stream info endpoint
    print("\n📊 Test 1: Checking stream info...")
    try:
        info_url = f"{base_url}/v0/api/cctv/cameras/{camera_id}/stream/info/"
        response = requests.get(info_url, timeout=10)
        
        if response.status_code == 200:
            info_data = response.json()
            print(f"✅ Stream info retrieved successfully")
            print(f"   Camera: {info_data.get('camera_name', 'Unknown')}")
            print(f"   Status: {info_data.get('status', 'Unknown')}")
            print(f"   Online: {info_data.get('is_online', False)}")
            print(f"   Streaming: {info_data.get('is_streaming', False)}")
        else:
            print(f"❌ Stream info failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Stream info request failed: {str(e)}")
        return False
    
    # Test 2: Test stream endpoint (short test)
    print("\n🎥 Test 2: Testing stream endpoint...")
    try:
        stream_url = f"{base_url}/v0/api/cctv/cameras/{camera_id}/stream/?quality=main"
        
        # Make a request with a short timeout to test if endpoint responds
        response = requests.get(stream_url, timeout=5, stream=True)
        
        if response.status_code == 200:
            print(f"✅ Stream endpoint is accessible")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"   Camera-Name: {response.headers.get('X-Camera-Name', 'Unknown')}")
            print(f"   Stream-Quality: {response.headers.get('X-Stream-Quality', 'Unknown')}")
            
            # Check if it's MJPEG stream
            content_type = response.headers.get('Content-Type', '')
            if 'multipart/x-mixed-replace' in content_type:
                print(f"✅ Correct MJPEG stream format detected")
            else:
                print(f"⚠️  Unexpected content type: {content_type}")
            
            # Read a small amount of data to test streaming
            data_chunk = next(response.iter_content(chunk_size=1024), b'')
            if data_chunk:
                print(f"✅ Stream data received ({len(data_chunk)} bytes)")
            else:
                print(f"⚠️  No stream data received")
                
        elif response.status_code == 503:
            print(f"⚠️  Camera not active (HTTP 503)")
            print(f"   Response: {response.text}")
        elif response.status_code == 404:
            print(f"❌ Camera not found (HTTP 404)")
            print(f"   Response: {response.text}")
        else:
            print(f"❌ Stream endpoint failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⚠️  Stream request timed out (this might be normal for streaming)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Stream request failed: {str(e)}")
        return False
    
    # Test 3: Test CORS headers
    print("\n🌐 Test 3: Testing CORS headers...")
    try:
        response = requests.options(stream_url, timeout=5)
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        if cors_headers['Access-Control-Allow-Origin'] == '*':
            print(f"✅ CORS headers configured correctly")
            for header, value in cors_headers.items():
                if value:
                    print(f"   {header}: {value}")
        else:
            print(f"⚠️  CORS headers may not be configured properly")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  CORS test failed: {str(e)}")
    
    print(f"\n🎉 Stream endpoint testing completed!")
    print(f"\n📝 To view the stream in a browser:")
    print(f"   {stream_url}")
    print(f"\n📝 Or use the test HTML file:")
    print(f"   Open Backend/test_stream.html in your browser")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_stream_endpoint.py <camera_id> [base_url]")
        print("Example: python test_stream_endpoint.py 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)
    
    camera_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    success = test_stream_endpoint(base_url, camera_id)
    sys.exit(0 if success else 1)
