"""
File Debugger Module - Tracks file operations and verifies file integrity
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

class FileDebugger:
    """Helper class to track file operations and verify file integrity"""
    
    def __init__(self, log_file="brochure_debug.log"):
        self.log_file = log_file
        self.operations = []
        self._clear_log()
        
    def _clear_log(self):
        """Clear previous log"""
        with open(self.log_file, 'w') as f:
            f.write(f"=== FILE DEBUG LOG STARTED AT {datetime.now()} ===\n")
    
    def _make_serializable(self, obj):
        """Recursively convert an object to JSON-serializable format"""
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj
    
    def log_operation(self, operation, file_path, details=None):
        """Log a file operation with timestamp and details"""
        # Convert file_path to string if it's a Path object
        if file_path and not isinstance(file_path, str):
            file_path = str(file_path)
        
        # Convert details to JSON-serializable format
        serializable_details = {}
        if details:
            for key, value in details.items():
                if isinstance(value, Path):
                    serializable_details[key] = str(value)
                elif isinstance(value, dict):
                    serializable_details[key] = self._make_serializable(value)
                else:
                    serializable_details[key] = value
        else:
            serializable_details = details
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "file": file_path if file_path else "None",
            "details": serializable_details or {},
            "exists": os.path.exists(file_path) if file_path else False,
            "size": os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0,
            "hash": self.get_file_hash(file_path) if file_path and os.path.exists(file_path) else None
        }
        self.operations.append(entry)
        
        # Write to log file immediately
        with open(self.log_file, 'a') as f:
            f.write(f"\n[{entry['timestamp']}] {operation}\n")
            f.write(f"  File: {entry['file']}\n")
            f.write(f"  Exists: {entry['exists']}\n")
            f.write(f"  Size: {entry['size']} bytes\n")
            f.write(f"  Hash: {entry['hash']}\n")
            if serializable_details:
                try:
                    f.write(f"  Details: {json.dumps(serializable_details, indent=2)}\n")
                except TypeError:
                    f.write(f"  Details: {str(serializable_details)}\n")
            f.write("-" * 80 + "\n")
    
    def get_file_hash(self, file_path):
        """Get file hash for verification"""
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
        except:
            return None
        return None