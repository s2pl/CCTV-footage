#!/usr/bin/env python3
"""
Simple Authentication Test for CCTV System
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/v0/api"
CREDENTIALS = {
    "email": "admin@admin.com",
    "password": "@Rishi21"
}

def test_auth():
    print("🔐 Testing Authentication...")
    print(f"📍 Server: {BASE_URL}")
    print(f"👤 User: {CREDENTIALS['email']}")
    print("=" * 50)
    
    try:
        # Test 1: Get JWT token
        print("\n1️⃣ Getting JWT token...")
        response = requests.post(
            f"{BASE_URL}/token/",
            json=CREDENTIALS,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Response: {json.dumps(data, indent=2)}")
            
            token = data.get('access')
            if token:
                print(f"   🔑 Token received: {token[:50]}...")
                
                # Test 2: Use token to access protected endpoint
                print("\n2️⃣ Testing protected endpoint...")
                headers = {'Authorization': f'Bearer {token}'}
                
                # Try health check first
                health_response = requests.get(f"{BASE_URL}/cctv/health", headers=headers)
                print(f"   Health Check Status: {health_response.status_code}")
                if health_response.status_code == 200:
                    print(f"   ✅ Health Check: {health_response.json()}")
                else:
                    print(f"   ❌ Health Check Failed: {health_response.text}")
                
                # Try multi-stream dashboard
                dashboard_response = requests.get(f"{BASE_URL}/cctv/cameras/multi-stream/", headers=headers)
                print(f"   Dashboard Status: {dashboard_response.status_code}")
                if dashboard_response.status_code == 200:
                    dashboard_data = dashboard_response.json()
                    print(f"   ✅ Dashboard: {json.dumps(dashboard_data, indent=2)}")
                else:
                    print(f"   ❌ Dashboard Failed: {dashboard_response.text}")
                
            else:
                print("   ❌ No access token in response")
                
        else:
            print(f"   ❌ Failed! Response: {response.text}")
            
    except Exception as e:
        print(f"   💥 Error: {e}")

if __name__ == "__main__":
    test_auth()
