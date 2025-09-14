#!/usr/bin/env python3
"""
Simple test script for CCTV streaming functionality
"""

import cv2
import time
import sys
import os

# Add the Backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Backend'))

def test_opencv_basic():
    """Test basic OpenCV functionality"""
    print("🔍 Testing OpenCV installation...")
    
    try:
        version = cv2.__version__
        print(f"✅ OpenCV version: {version}")
        
        # Test basic operations
        test_array = cv2.imread("Backend/media/logo/logo.png")
        if test_array is not None:
            print("✅ OpenCV image reading: OK")
            print(f"   Image shape: {test_array.shape}")
        else:
            print("⚠️ OpenCV image reading: Test image not found")
            
    except Exception as e:
        print(f"❌ OpenCV error: {str(e)}")
        return False
    
    return True

def test_camera_connection(rtsp_url):
    """Test connection to a camera"""
    print(f"\n🔌 Testing camera connection: {rtsp_url}")
    
    try:
        # Create video capture
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            print("❌ Failed to open video capture")
            return False
        
        # Set buffer size
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        print("✅ Video capture opened successfully")
        
        # Test frame reading
        print("📸 Testing frame reading...")
        
        for attempt in range(3):
            try:
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    print(f"✅ Frame {attempt + 1} read successfully")
                    print(f"   Frame shape: {frame.shape}")
                    print(f"   Frame size: {frame.size}")
                    
                    # Test frame encoding
                    try:
                        encode_ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if encode_ret:
                            print(f"✅ Frame {attempt + 1} encoded successfully")
                            print(f"   Encoded size: {len(buffer)} bytes")
                        else:
                            print(f"❌ Frame {attempt + 1} encoding failed")
                    except Exception as e:
                        print(f"❌ Frame {attempt + 1} encoding error: {str(e)}")
                    
                    break
                else:
                    print(f"⚠️ Frame {attempt + 1} read failed")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Frame {attempt + 1} read error: {str(e)}")
                time.sleep(1)
        
        # Clean up
        cap.release()
        print("🛑 Video capture released")
        
        return True
        
    except Exception as e:
        print(f"❌ Camera connection error: {str(e)}")
        return False

def test_streaming_loop(rtsp_url, duration_seconds=10):
    """Test continuous streaming for a specified duration"""
    print(f"\n🎬 Testing streaming loop for {duration_seconds} seconds...")
    
    try:
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            print("❌ Failed to open video capture")
            return False
        
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        start_time = time.time()
        frame_count = 0
        error_count = 0
        
        print("🔄 Starting streaming loop...")
        
        while (time.time() - start_time) < duration_seconds:
            try:
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    frame_count += 1
                    
                    if frame_count % 10 == 0:
                        elapsed = time.time() - start_time
                        fps = frame_count / elapsed
                        print(f"   Frame {frame_count}, FPS: {fps:.1f}, Elapsed: {elapsed:.1f}s")
                        
                else:
                    error_count += 1
                    print(f"   Frame read failed (error #{error_count})")
                    
                    if error_count >= 5:
                        print("❌ Too many consecutive errors, stopping")
                        break
                
                time.sleep(0.04)  # ~25 FPS
                
            except Exception as e:
                error_count += 1
                print(f"   Streaming error (error #{error_count}): {str(e)}")
                
                if error_count >= 5:
                    print("❌ Too many consecutive errors, stopping")
                    break
                
                time.sleep(0.1)
        
        # Final statistics
        elapsed = time.time() - start_time
        if elapsed > 0:
            fps = frame_count / elapsed
            print(f"\n📊 Streaming Statistics:")
            print(f"   Total frames: {frame_count}")
            print(f"   Total errors: {error_count}")
            print(f"   Duration: {elapsed:.1f} seconds")
            print(f"   Average FPS: {fps:.1f}")
            print(f"   Success rate: {(frame_count / (frame_count + error_count) * 100):.1f}%")
        
        cap.release()
        print("🛑 Streaming test completed")
        
        return frame_count > 0
        
    except Exception as e:
        print(f"❌ Streaming loop error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🔍 CCTV Streaming Test Tool")
    print("=" * 40)
    
    # Test OpenCV
    if not test_opencv_basic():
        print("\n❌ OpenCV test failed, cannot continue")
        return
    
    # Test camera connection (replace with your camera URL)
    rtsp_url = "rtsp://admin@192.168.1.162:554/live/0/MAIN"
    
    if test_camera_connection(rtsp_url):
        print("\n✅ Camera connection test passed")
        
        # Test streaming loop
        if test_streaming_loop(rtsp_url, duration_seconds=15):
            print("\n✅ Streaming test passed")
        else:
            print("\n❌ Streaming test failed")
    else:
        print("\n❌ Camera connection test failed")
    
    print("\n🏁 Test completed")

if __name__ == "__main__":
    main()
