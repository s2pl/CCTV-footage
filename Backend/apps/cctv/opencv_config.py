"""
OpenCV configuration and optimization settings for CCTV streaming
"""

import logging
import os
import warnings

# Suppress OpenCV warnings before importing cv2
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*FFMPEG.*')
warnings.filterwarnings('ignore', message='.*codec.*')
warnings.filterwarnings('ignore', message='.*tag.*')
warnings.filterwarnings('ignore', message='.*fallback.*')

import cv2

# Suppress cv2 logging
logging.getLogger('cv2').setLevel(logging.ERROR)
logging.getLogger().setLevel(logging.WARNING)  # Don't let cv2 messages through

# Set environment variables to prevent FFmpeg threading issues
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'threads;1|timeout;5000000'
os.environ['OPENCV_FFMPEG_WRITER_OPTIONS'] = 'threads;1'

# Disable FFmpeg multi-threading to prevent assertion errors
os.environ['FFMPEG_THREAD_TYPE'] = 'none'

# Additional OpenCV optimizations for Windows
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'  # Reduce OpenCV logging
os.environ['OPENCV_VIDEOIO_PRIORITY_FFMPEG'] = '1000'  # Prioritize FFmpeg backend

# Suppress FFMPEG warnings and errors
os.environ['FFMPEG_LOGLEVEL'] = 'quiet'  # Suppress FFMPEG output
os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '1'  # Reduce read attempts

logger = logging.getLogger(__name__)

# Cache for tested codecs to avoid repeated testing
_codec_cache = {}
_cache_lock = None

def _get_cache_lock():
    """Get or create thread lock for codec cache"""
    global _cache_lock
    if _cache_lock is None:
        import threading
        _cache_lock = threading.Lock()
    return _cache_lock

# OpenCV backend preferences for better performance
OPENCV_BACKENDS = [
    cv2.CAP_FFMPEG,      # FFMPEG backend (recommended for RTSP)
    cv2.CAP_GSTREAMER,   # GStreamer backend
    cv2.CAP_ANY          # Any available backend
]

# Buffer and performance settings
STREAM_SETTINGS = {
    'buffer_size': 1,           # Minimize buffer for low latency
    'fps': 25,                  # Target FPS
    'frame_width': 1920,        # Max frame width
    'frame_height': 1080,       # Max frame height
    'timeout_ms': 10000,        # Connection timeout in milliseconds (increased)
    'retry_attempts': 5,        # Number of retry attempts (increased)
    'retry_delay': 2.0,         # Delay between retries in seconds (increased)
    'read_timeout': 5000,       # Frame read timeout in milliseconds
    'reconnect_delay': 5.0,     # Delay before reconnecting after failure
}

# JPEG encoding settings for streaming
JPEG_ENCODING_SETTINGS = [
    cv2.IMWRITE_JPEG_QUALITY, 85,      # Quality (0-100)
    cv2.IMWRITE_JPEG_OPTIMIZE, 1,      # Enable optimization
    cv2.IMWRITE_JPEG_PROGRESSIVE, 0,   # Progressive JPEG (0 for streaming)
]

# Video codec settings for recording
# Prioritize well-supported codecs to avoid OpenCV/FFMPEG errors
# Include more codec options for better compatibility
RECORDING_CODECS = [
    ('mp4v', '.mp4', 'MPEG-4 MP4 - Most reliable codec for Windows'),
    ('MJPG', '.mp4', 'Motion JPEG MP4 - Reliable fallback format'),
    ('XVID', '.mp4', 'Xvid MP4 - High quality fallback'),
    ('DIVX', '.mp4', 'DivX MP4 - Alternative codec'),
    ('WMV1', '.wmv', 'Windows Media Video - Windows native'),
    ('WMV2', '.wmv', 'Windows Media Video 2 - Windows native'),
    # AVI fallback (only if all MP4 options fail)
    ('MJPG', '.avi', 'Motion JPEG AVI - Last resort fallback'),
    ('XVID', '.avi', 'Xvid AVI - Last resort fallback'),
    ('DIVX', '.avi', 'DivX AVI - Last resort fallback'),
]

def get_optimal_backend():
    """Get the best available OpenCV backend for RTSP streaming"""
    # Skip backend testing as it causes read-only property errors
    # Just return the first backend and let OpenCV handle it
    logger.info("Using default OpenCV backend (avoiding backend property errors)")
    return cv2.CAP_ANY

def configure_video_capture(cap, rtsp_url):
    """Configure video capture with optimal settings for RTSP streaming"""
    try:
        # Skip problematic backend setting that causes read-only property errors
        logger.debug("Configuring video capture with safe settings")
        
        # Apply only essential settings with error handling
        safe_properties = [
            (cv2.CAP_PROP_BUFFERSIZE, 1, "buffer size"),
        ]
        
        # Add CAP_PROP_THREADS only if it exists in this OpenCV version
        if hasattr(cv2, 'CAP_PROP_THREADS'):
            safe_properties.append((cv2.CAP_PROP_THREADS, 1, "thread count"))
        else:
            logger.debug("CAP_PROP_THREADS not available in this OpenCV version")
        
        for prop, value, name in safe_properties:
            try:
                cap.set(prop, value)
                logger.debug(f"Set {name} to {value}")
            except Exception as e:
                logger.debug(f"Could not set {name}: {str(e)}")
        
        # RTSP-specific optimizations with error handling
        if 'rtsp://' in rtsp_url.lower():
            try:
                # Check if RTSP properties are available before using them
                if hasattr(cv2, 'CAP_PROP_RTSP_TRANSPORT') and hasattr(cv2, 'CAP_RTSP_TRANSPORT_TCP'):
                    # Force TCP transport to avoid UDP issues
                    cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_RTSP_TRANSPORT_TCP)
                    logger.debug("Set RTSP transport to TCP")
                else:
                    logger.debug("RTSP transport properties not available in this OpenCV version")
            except Exception as e:
                logger.debug(f"Could not set RTSP transport: {str(e)}")
        
        logger.info("Video capture configured with safe settings")
        return True
        
    except Exception as e:
        logger.error(f"Error configuring video capture: {str(e)}")
        return False

def test_camera_connection_robust(rtsp_url, max_attempts=None):
    """Test camera connection with multiple attempts and better error handling"""
    if max_attempts is None:
        max_attempts = STREAM_SETTINGS['retry_attempts']
    
    for attempt in range(max_attempts):
        try:
            cap = cv2.VideoCapture(rtsp_url)
            
            if not cap.isOpened():
                logger.warning(f"Attempt {attempt + 1}: Failed to open capture")
                cap.release()
                continue
            
            # Configure capture
            configure_video_capture(cap, rtsp_url)
            
            # Test frame reading
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                logger.info(f"Camera connection successful on attempt {attempt + 1}")
                return True, "Connection successful"
            else:
                logger.warning(f"Attempt {attempt + 1}: No frames received")
                
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}: Connection error - {str(e)}")
        
        # Wait before retry
        if attempt < max_attempts - 1:
            import time
            time.sleep(STREAM_SETTINGS['retry_delay'])
    
    return False, f"Failed to connect after {max_attempts} attempts"

def get_frame_with_timeout(cap, timeout_ms=1000):
    """Get a frame with timeout to prevent hanging"""
    import time
    import threading
    
    result = {'ret': False, 'frame': None, 'done': False}
    
    def read_frame():
        try:
            ret, frame = cap.read()
            result['ret'] = ret
            result['frame'] = frame
        except Exception as e:
            logger.warning(f"Frame read error: {str(e)}")
        finally:
            result['done'] = True
    
    # Start reading in a separate thread
    thread = threading.Thread(target=read_frame, daemon=True)
    thread.start()
    
    # Wait for result with timeout
    start_time = time.time()
    while not result['done'] and (time.time() - start_time) * 1000 < timeout_ms:
        time.sleep(0.01)
    
    if result['done']:
        return result['ret'], result['frame']
    else:
        logger.warning("Frame read timeout")
        return False, None

def safe_frame_encoding(frame, quality=85):
    """Safely encode a frame to JPEG with error handling"""
    try:
        if frame is None:
            return False, None
        
        # Check frame dimensions
        height, width = frame.shape[:2]
        if width <= 0 or height <= 0:
            logger.warning("Invalid frame dimensions")
            return False, None
        
        # Encode with quality settings
        encoding_params = JPEG_ENCODING_SETTINGS.copy()
        encoding_params[1] = quality  # Update quality
        
        ret, buffer = cv2.imencode('.jpg', frame, encoding_params)
        return ret, buffer
        
    except Exception as e:
        logger.error(f"Frame encoding error: {str(e)}")
        return False, None

def cleanup_capture(cap):
    """Safely cleanup video capture object"""
    try:
        if cap is not None:
            cap.release()
    except Exception as e:
        logger.error(f"Error releasing capture: {str(e)}")

def get_opencv_info():
    """Get OpenCV version and build information"""
    info = {
        'version': cv2.__version__,
        'build_info': cv2.getBuildInformation(),
        'available_backends': [],
        'available_properties': {
            'CAP_PROP_THREADS': hasattr(cv2, 'CAP_PROP_THREADS'),
            'CAP_PROP_RTSP_TRANSPORT': hasattr(cv2, 'CAP_PROP_RTSP_TRANSPORT'),
            'CAP_RTSP_TRANSPORT_TCP': hasattr(cv2, 'CAP_RTSP_TRANSPORT_TCP'),
            'CAP_PROP_BUFFERSIZE': hasattr(cv2, 'CAP_PROP_BUFFERSIZE'),
        }
    }
    
    # Test available backends
    for backend in OPENCV_BACKENDS:
        try:
            cap = cv2.VideoCapture()
            cap.set(cv2.CAP_PROP_BACKEND, backend)
            if cap.isOpened():
                info['available_backends'].append(backend)
            cap.release()
        except:
            pass
    
    return info

def check_opencv_compatibility():
    """Check OpenCV compatibility and log important information"""
    try:
        info = get_opencv_info()
        logger.info(f"OpenCV version: {info['version']}")
        logger.info(f"Available properties: {info['available_properties']}")
        
        # Log warnings for missing critical properties
        if not info['available_properties']['CAP_PROP_THREADS']:
            logger.warning("CAP_PROP_THREADS not available - threading optimization disabled")
        if not info['available_properties']['CAP_PROP_RTSP_TRANSPORT']:
            logger.warning("RTSP transport control not available - may have connection issues")
            
        return True
    except Exception as e:
        logger.error(f"OpenCV compatibility check failed: {str(e)}")
        return False

def monitor_stream_health(cap, camera_name="Unknown"):
    """Monitor stream health and return diagnostic information"""
    try:
        if not cap or not cap.isOpened():
            return {
                'status': 'error',
                'message': 'Capture not opened',
                'fps': 0,
                'frame_count': 0
            }
        
        # Get basic properties
        fps = cap.get(cv2.CAP_PROP_FPS) if hasattr(cv2, 'CAP_PROP_FPS') else 0
        frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) if hasattr(cv2, 'CAP_PROP_FRAME_WIDTH') else 0
        frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) if hasattr(cv2, 'CAP_PROP_FRAME_HEIGHT') else 0
        
        # Try to read a frame to test connectivity
        ret, frame = cap.read()
        
        if ret and frame is not None:
            return {
                'status': 'healthy',
                'message': 'Stream is active and receiving frames',
                'fps': fps,
                'resolution': f"{int(frame_width)}x{int(frame_height)}",
                'frame_shape': frame.shape if frame is not None else None
            }
        else:
            return {
                'status': 'warning',
                'message': 'Cannot read frames from stream',
                'fps': fps,
                'resolution': f"{int(frame_width)}x{int(frame_height)}"
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'fps': 0
        }

def test_codec_compatibility(width, height, fps=25, test_frame=None):
    """Test which codecs are available and working on the current system"""
    import tempfile
    import numpy as np
    
    if test_frame is None:
        # Create a simple test frame if none provided
        test_frame = np.zeros((height, width, 3), dtype=np.uint8)
        test_frame[:] = (50, 100, 150)  # Fill with a color
    
    working_codecs = []
    
    # Temporarily suppress OpenCV and FFMPEG logging during testing
    old_log_level = os.environ.get('OPENCV_LOG_LEVEL', 'INFO')
    old_ffmpeg_log_level = os.environ.get('FFMPEG_LOGLEVEL', 'info')
    os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'  # Less strict than FATAL
    os.environ['FFMPEG_LOGLEVEL'] = 'error'   # Less strict than quiet
    
    try:
        for codec, extension, description in RECORDING_CODECS:
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # Test the codec with better error handling
                fourcc = cv2.VideoWriter_fourcc(*codec)
                writer = None
                success = False
                
                try:
                    writer = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
                    
                    if writer.isOpened():
                        # Try to write a few frames
                        success = True
                        for i in range(3):
                            try:
                                writer.write(test_frame)
                            except Exception:
                                success = False
                                break
                        
                        # Check if file was created (be more lenient with size requirements)
                        if success and os.path.exists(temp_path) and os.path.getsize(temp_path) > 50:
                            working_codecs.append((codec, extension, description))
                            logger.info(f"✅ Codec {codec} works: {description}")
                        else:
                            logger.debug(f"❌ Codec {codec} test failed: file not created or too small")
                    else:
                        logger.debug(f"❌ Codec {codec} failed to open writer")
                        
                except Exception as e:
                    logger.debug(f"❌ Codec {codec} failed with error: {str(e)}")
                finally:
                    if writer is not None:
                        try:
                            writer.release()
                        except:
                            pass
                
                # Clean up
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
                    
            except Exception as e:
                logger.debug(f"❌ Codec {codec} failed with error: {str(e)}")
    
    finally:
        # Restore original log levels
        os.environ['OPENCV_LOG_LEVEL'] = old_log_level
        os.environ['FFMPEG_LOGLEVEL'] = old_ffmpeg_log_level
    
    # If no codecs work, add a basic fallback
    if not working_codecs:
        logger.warning("No codecs passed testing, adding basic fallback")
        working_codecs = [('MJPG', '.avi', 'Motion JPEG AVI - Basic fallback')]
    
    logger.info(f"Found {len(working_codecs)} working codecs out of {len(RECORDING_CODECS)} tested")
    return working_codecs

def get_cached_working_codecs(width, height, fps=25, test_frame=None):
    """Get working codecs from cache or test them if not cached"""
    cache_key = f"{width}x{height}@{fps}"
    
    with _get_cache_lock():
        if cache_key in _codec_cache:
            logger.debug(f"Using cached codec results for {cache_key}")
            return _codec_cache[cache_key]
        
        logger.info(f"Testing codecs for {cache_key} (first time)")
        working_codecs = test_codec_compatibility(width, height, fps, test_frame)
        
        # Cache the results
        _codec_cache[cache_key] = working_codecs
        logger.info(f"Cached {len(working_codecs)} working codecs for {cache_key}")
        
        return working_codecs

def clear_codec_cache():
    """Clear the codec cache (useful for testing or when codec priorities change)"""
    global _codec_cache
    with _get_cache_lock():
        _codec_cache.clear()
        logger.info("Codec cache cleared - will test codecs with new priorities")

def optimize_capture_for_streaming(cap, rtsp_url):
    """Apply streaming-specific optimizations to video capture"""
    try:
        # Configure for streaming performance
        configure_video_capture(cap, rtsp_url)
        
        # Additional streaming optimizations
        streaming_props = []
        
        # Apply frame size limits for better performance
        if hasattr(cv2, 'CAP_PROP_FRAME_WIDTH') and hasattr(cv2, 'CAP_PROP_FRAME_HEIGHT'):
            try:
                current_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                current_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                
                # Limit resolution for better streaming performance
                max_width = STREAM_SETTINGS['frame_width']
                max_height = STREAM_SETTINGS['frame_height']
                
                if current_width > max_width or current_height > max_height:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, max_width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, max_height)
                    logger.debug(f"Limited resolution from {int(current_width)}x{int(current_height)} to {max_width}x{max_height}")
                    
            except Exception as res_error:
                logger.debug(f"Could not set resolution limits: {str(res_error)}")
        
        for prop, value in streaming_props:
            try:
                cap.set(prop, value)
            except Exception as prop_error:
                logger.debug(f"Could not set streaming property {prop}: {str(prop_error)}")
        
        logger.info("Applied streaming optimizations")
        return True
        
    except Exception as e:
        logger.error(f"Error applying streaming optimizations: {str(e)}")
        return False
