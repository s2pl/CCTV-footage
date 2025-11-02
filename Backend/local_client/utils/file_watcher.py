"""
File watcher for monitoring recording directory
"""
import os
import time
from pathlib import Path
from typing import List, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class FileWatcher:
    """Monitor directory for new files"""
    
    def __init__(self, directory: Path, callback: Callable, check_interval: float = 5.0):
        """
        Initialize file watcher
        
        Args:
            directory: Directory to watch
            callback: Callback function(file_path: Path) when new file is detected
            check_interval: How often to check for new files (seconds)
        """
        self.directory = Path(directory)
        self.callback = callback
        self.check_interval = check_interval
        self.known_files = set()
        self.running = False
        
        # Initialize known files
        if self.directory.exists():
            self.known_files = set(self.directory.rglob('*'))
    
    def start(self):
        """Start watching"""
        self.running = True
        logger.info(f"Started watching directory: {self.directory}")
        
        while self.running:
            try:
                self._check_new_files()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in file watcher: {str(e)}")
                time.sleep(self.check_interval)
    
    def stop(self):
        """Stop watching"""
        self.running = False
        logger.info("Stopped file watcher")
    
    def _check_new_files(self):
        """Check for new files and trigger callbacks"""
        if not self.directory.exists():
            return
        
        current_files = set(self.directory.rglob('*'))
        new_files = current_files - self.known_files
        
        # Filter out directories and temporary files
        new_files = {f for f in new_files if f.is_file() and not f.name.endswith('.tmp')}
        
        for file_path in new_files:
            try:
                # Wait a bit to ensure file is fully written
                time.sleep(0.5)
                if file_path.exists() and file_path.stat().st_size > 0:
                    logger.info(f"New file detected: {file_path}")
                    self.callback(file_path)
            except Exception as e:
                logger.error(f"Error processing new file {file_path}: {str(e)}")
        
        self.known_files = current_files

