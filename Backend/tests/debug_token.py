#!/usr/bin/env python3
"""
Debug JWT Token Issues
"""

import requests
import json
import jwt
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/v0/api"
CREDENTIALS = {
    "email": "admin@admin.com",
    "password": "@Rishi21"
}

def decode_token_without_verification(token):
    """Decode JWT token without verification to see payload"""
    try:
        # Split the token and get the payload part
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (second part)
        import base64
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded.decode('utf-8'))
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def test_token_debug():
    print("🔍 Debugging JWT Token...")
    print("=" * 50)
    
    try:
        # Get JWT token
        print("1️⃣ Getting JWT token...")
        response = requests.post(
            f"{BASE_URL}/token/",
            json=CREDENTIALS,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            
            if token:
                print(f"✅ Token received: {token[:50]}...")
                
                # Decode token payload
                print("\n2️⃣ Decoding token payload...")
                payload = decode_token_without_verification(token)
                if payload:
                    print(f"   Token Payload:")
                    print(f"   - User ID: {payload.get('user_id')}")
                    print(f"   - Email: {payload.get('email')}")
                    print(f"   - Role: {payload.get('role')}")
                    print(f"   - Type: {payload.get('type')}")
                    print(f"   - Expires: {datetime.fromtimestamp(payload.get('exp')).isoformat()}")
                    print(f"   - Issued: {datetime.fromtimestamp(payload.get('iat')).isoformat()}")
                
                # Test with different header formats
                print("\n3️⃣ Testing different authentication headers...")
                
                headers_variations = [
                    {'Authorization': f'Bearer {token}'},
                    {'Authorization': f'bearer {token}'},
                    {'Authorization': f'BEARER {token}'},
                    {'HTTP_AUTHORIZATION': f'Bearer {token}'},
                ]
                
                for i, headers in enumerate(headers_variations, 1):
                    print(f"   Test {i}: {list(headers.keys())[0]}")
                    try:
                        response = requests.get(f"{BASE_URL}/cctv/health", headers=headers)
                        print(f"      Status: {response.status_code}")
                        if response.status_code == 200:
                            print(f"      ✅ Success!")
                        else:
                            print(f"      ❌ Failed: {response.text[:100]}")
                    except Exception as e:
                        print(f"      💥 Error: {e}")
                
                # Test the multi-stream endpoint
                print("\n4️⃣ Testing multi-stream endpoint...")
                headers = {'Authorization': f'Bearer {token}'}
                response = requests.get(f"{BASE_URL}/cctv/cameras/multi-stream/", headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Success! Found {len(data.get('cameras', []))} cameras")
                else:
                    print(f"   ❌ Failed: {response.text}")
                
            else:
                print("❌ No access token received")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_token_debug()
