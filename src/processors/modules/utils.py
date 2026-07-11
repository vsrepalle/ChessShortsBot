"""
Utility Module - Common utility functions
"""

import os
import sys
import subprocess
from pathlib import Path

class Utils:
    """Utility functions for the processor"""
    
    @staticmethod
    def preview_video(video_path):
        """Open video for preview"""
        try:
            if sys.platform == 'win32':
                os.startfile(video_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', video_path])
            else:
                subprocess.run(['xdg-open', video_path])
            return True
        except Exception as e:
            print(f"⚠️ Could not auto-open video: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path):
        """Get file size in bytes"""
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
    
    @staticmethod
    def get_file_name(file_path):
        """Get filename without extension"""
        return Path(file_path).stem