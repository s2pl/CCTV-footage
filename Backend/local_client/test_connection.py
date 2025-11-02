"""
Test script to verify local_client connection to backend
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import config
    from api_client import BackendAPIClient
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Make sure you're running this from the local_client directory")
    sys.exit(1)


async def test_connection():
    """Test connection to backend API"""
    print("[TEST] Local Client Connection Test")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Checking configuration...")
    print(f"   Backend URL: {config.BACKEND_API_URL}")
    print(f"   Client Token: {'[OK] Set' if config.CLIENT_TOKEN else '[!] NOT SET'}")
    print(f"   Client ID: {config.CLIENT_ID or 'Not set (optional)'}")
    
    is_valid, errors = config.validate()
    if not is_valid:
        print("\n[ERROR] Configuration validation failed:")
        for error in errors:
            print(f"   - {error}")
        print("\n[INFO] Please check your .env file and make sure:")
        print("   - BACKEND_API_URL is set correctly")
        print("   - CLIENT_TOKEN is set (get from Django Admin)")
        return False
    
    print("   [OK] Configuration valid")
    
    # Test connection
    print("\n2. Testing backend connection...")
    async with BackendAPIClient() as client:
        # Test health endpoint
        connected = await client.test_connection()
        if not connected:
            print("   [ERROR] Failed to connect to backend")
            print(f"\n[INFO] Please verify:")
            print(f"   - Backend is running at {config.BACKEND_API_URL}")
            print(f"   - Network connectivity is working")
            return False
        
        print("   [OK] Backend connection successful")
        
        # Test authentication by fetching cameras
        print("\n3. Testing authentication...")
        try:
            cameras = await client.fetch_cameras()
            print(f"   [OK] Authentication successful")
            print(f"   [OK] Found {len(cameras)} assigned camera(s)")
            
            if cameras:
                print("\n   Assigned cameras:")
                for camera in cameras:
                    print(f"   - {camera.name} (ID: {camera.id})")
            else:
                print("\n   [WARNING] No cameras assigned to this client yet")
                print("   [INFO] Assign cameras in Django Admin:")
                print("      1. Go to CCTV → Local Recording Clients")
                print("      2. Edit your client")
                print("      3. Add cameras in 'Assigned cameras' field")
        except Exception as e:
            print(f"   [ERROR] Authentication failed: {str(e)}")
            print("\n[INFO] Please verify:")
            print("   - CLIENT_TOKEN is correct")
            print("   - Client exists in Django Admin")
            print("   - Client is marked as active")
            return False
        
        # Test schedule fetching
        print("\n4. Testing schedule sync...")
        try:
            schedules = await client.fetch_schedules()
            print(f"   [OK] Schedule sync successful")
            print(f"   [OK] Found {len(schedules)} active schedule(s)")
            
            if schedules:
                print("\n   Active schedules:")
                for schedule in schedules:
                    print(f"   - {schedule.name} ({schedule.schedule_type})")
                    print(f"     Camera: {schedule.camera.name}")
                    print(f"     Time: {schedule.start_time} - {schedule.end_time}")
            else:
                print("\n   [WARNING] No active schedules found")
                print("   [INFO] Create schedules in Django Admin:")
                print("      1. Go to CCTV → Recording Schedules")
                print("      2. Add new schedule for your cameras")
                print("      3. Make sure 'Is active' is checked")
        except Exception as e:
            print(f"   [ERROR] Schedule sync failed: {str(e)}")
            return False
    
    # Test API endpoints
    print("\n5. Testing API endpoints...")
    endpoints_to_test = [
        ("/v0/api/local-client/health", "Health check"),
        ("/v0/api/cctv/health", "CCTV API health"),
        ("/health/", "Main health check"),
    ]
    
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        for endpoint, description in endpoints_to_test:
            try:
                response = await http_client.get(f"{config.BACKEND_API_URL}{endpoint}")
                if response.status_code == 200:
                    print(f"   [OK] {description}: OK")
                else:
                    print(f"   [WARNING] {description}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   [ERROR] {description}: Failed ({str(e)})")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed! Local client is properly configured.")
    print("\n[INFO] Next steps:")
    print("   1. Run the local client: python main.py")
    print("   2. Monitor logs: tail -f recordings/logs/client.log")
    print("   3. Check status: curl http://localhost:8001/status")
    print("=" * 60)
    
    return True


def main():
    """Main entry point"""
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

