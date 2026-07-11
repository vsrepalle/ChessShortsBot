"""
Upload Debugger Module - Detailed logging for upload process
"""

import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime

class UploadDebugger:
    """Detailed debugger for upload process"""
    
    def __init__(self, log_file="upload_debug.log"):
        self.log_file = log_file
        self.start_time = datetime.now()
        self.steps = []
        self.errors = []
        
        self._clear_log()
        self.log("=" * 80)
        self.log(f"UPLOAD DEBUGGER STARTED AT {self.start_time}")
        self.log("=" * 80)
        self.log(f"Python version: {sys.version}")
        self.log(f"Current directory: {os.getcwd()}")
        self.log("=" * 80)
    
    def _clear_log(self):
        try:
            with open(self.log_file, 'w') as f:
                f.write("")
        except:
            pass
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        self.steps.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except:
            pass
        
        print(log_entry)
    
    def log_step(self, step_name, details=None):
        self.log(f"▶ STEP: {step_name}")
        if details:
            try:
                self.log(f"   Details: {json.dumps(details, indent=2, default=str)}")
            except:
                self.log(f"   Details: {details}")
        self.log("-" * 40)
    
    def log_error(self, error, context=None):
        error_msg = str(error)
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "error": error_msg,
            "context": context,
            "traceback": traceback.format_exc()
        })
        
        self.log(f"❌ ERROR: {error_msg}", "ERROR")
        if context:
            self.log(f"   Context: {context}", "ERROR")
        self.log(f"   Traceback: {traceback.format_exc()}", "ERROR")
    
    def log_success(self, message):
        self.log(f"✅ SUCCESS: {message}", "SUCCESS")
    
    def log_file_info(self, file_path, label="File"):
        if not file_path:
            self.log(f"   {label}: None (not provided)", "WARNING")
            return
        
        file_path = str(file_path)
        exists = os.path.exists(file_path)
        size = os.path.getsize(file_path) if exists else 0
        
        self.log(f"   {label}: {file_path}")
        self.log(f"   Exists: {exists}")
        self.log(f"   Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
        
        if exists:
            mod_time = os.path.getmtime(file_path)
            mod_datetime = datetime.fromtimestamp(mod_time)
            self.log(f"   Modified: {mod_datetime}")
    
    def log_metadata(self, metadata, label="Metadata"):
        self.log(f"   {label}:")
        if metadata:
            for key, value in metadata.items():
                if value:
                    if isinstance(value, str) and len(value) > 200:
                        value = value[:200] + "..."
                    self.log(f"      {key}: {value}")
        else:
            self.log(f"      No metadata provided")
    
    def save_summary(self):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        summary = []
        summary.append("=" * 80)
        summary.append("UPLOAD SUMMARY")
        summary.append("=" * 80)
        summary.append(f"Start time: {self.start_time}")
        summary.append(f"End time: {end_time}")
        summary.append(f"Duration: {duration:.2f} seconds")
        summary.append(f"Steps logged: {len(self.steps)}")
        summary.append(f"Errors: {len(self.errors)}")
        
        if self.errors:
            summary.append("-" * 40)
            summary.append("ERROR SUMMARY:")
            for i, error in enumerate(self.errors, 1):
                summary.append(f"  {i}. {error['error']}")
        
        summary.append("=" * 80)
        
        summary_text = "\n".join(summary)
        self.log(summary_text)
        
        try:
            with open("upload_summary.txt", 'w', encoding='utf-8') as f:
                f.write(summary_text)
                f.write("\n\n")
                f.write("Full log:\n")
                f.write("=" * 80)
                for step in self.steps:
                    f.write(f"[{step['timestamp']}] [{step['level']}] {step['message']}\n")
        except:
            pass
        
        return summary_text
