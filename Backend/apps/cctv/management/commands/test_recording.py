"""
Management command to test video recording functionality
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import tempfile
import logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test video recording functionality with a synthetic video'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing video recording functionality...'))
        
        try:
            import cv2
            from apps.cctv.opencv_config import test_codec_compatibility
            
            # Test parameters
            width, height, fps = 640, 480, 25
            duration_seconds = 3
            total_frames = fps * duration_seconds
            
            self.stdout.write(f"Creating test video: {width}x{height} @ {fps}fps for {duration_seconds}s ({total_frames} frames)")
            
            # Get working codecs
            working_codecs = test_codec_compatibility(width, height, fps)
            
            if not working_codecs:
                self.stdout.write(self.style.ERROR('No working codecs found!'))
                return
            
            # Use the first working codec
            codec, extension, description = working_codecs[0]
            self.stdout.write(f"Using codec: {codec} ({description})")
            
            # Create test recording directory
            test_dir = os.path.join(settings.MEDIA_ROOT, 'test_recordings')
            os.makedirs(test_dir, exist_ok=True)
            
            # Create test video file
            test_filename = f"test_recording{extension}"
            test_filepath = os.path.join(test_dir, test_filename)
            
            # Remove existing test file
            if os.path.exists(test_filepath):
                os.remove(test_filepath)
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(test_filepath, fourcc, fps, (width, height))
            
            if not out.isOpened():
                self.stdout.write(self.style.ERROR(f'Failed to open video writer for {codec}'))
                return
            
            self.stdout.write("Writing test frames...")
            
            # Generate and write test frames
            frames_written = 0
            for frame_num in range(total_frames):
                # Create a colorful test frame
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                
                # Create moving colored rectangles
                color_r = int(127 + 127 * np.sin(frame_num * 0.1))
                color_g = int(127 + 127 * np.sin(frame_num * 0.15))
                color_b = int(127 + 127 * np.sin(frame_num * 0.2))
                
                # Draw colored background
                frame[:] = (color_b, color_g, color_r)
                
                # Add frame counter text
                cv2.putText(frame, f'Frame {frame_num+1}/{total_frames}', 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Add moving rectangle
                rect_x = int((width - 100) * (frame_num / total_frames))
                cv2.rectangle(frame, (rect_x, height//2 - 25), (rect_x + 100, height//2 + 25), (0, 255, 255), -1)
                
                # Write frame
                out.write(frame)
                frames_written += 1
                
                if frame_num % fps == 0:  # Progress every second
                    self.stdout.write(f"  Written {frames_written} frames...")
            
            # Release writer
            out.release()
            
            # Check result
            if os.path.exists(test_filepath):
                file_size = os.path.getsize(test_filepath)
                self.stdout.write(self.style.SUCCESS(f'✅ Test recording completed successfully!'))
                self.stdout.write(f'  File: {test_filepath}')
                self.stdout.write(f'  Size: {file_size:,} bytes')
                self.stdout.write(f'  Frames written: {frames_written}')
                
                # Verify video can be read back
                self.stdout.write("Verifying recorded video...")
                cap = cv2.VideoCapture(test_filepath)
                if cap.isOpened():
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    video_fps = cap.get(cv2.CAP_PROP_FPS)
                    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    self.stdout.write(f'  Video properties: {video_width}x{video_height} @ {video_fps}fps')
                    self.stdout.write(f'  Frame count: {frame_count}')
                    
                    # Read a few frames to verify
                    frames_read = 0
                    while frames_read < 5:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        frames_read += 1
                    
                    cap.release()
                    
                    if frames_read > 0:
                        self.stdout.write(self.style.SUCCESS(f'✅ Video verification successful! Read {frames_read} frames.'))
                    else:
                        self.stdout.write(self.style.WARNING('⚠️ Could not read frames from recorded video'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️ Could not open recorded video for verification'))
                
            else:
                self.stdout.write(self.style.ERROR('❌ Test recording file was not created'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during recording test: {str(e)}'))
            logger.exception("Recording test failed")
