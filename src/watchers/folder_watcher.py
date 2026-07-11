"""
Folder Watcher Module - Monitors folders for new files
"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FolderWatcherHandler(FileSystemEventHandler):
    """Handler for folder watcher events"""
    
    def __init__(self, callback):
        self.callback = callback
        self.processed_files = set()
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            # Wait a moment for file to be fully written
            time.sleep(0.5)
            self.callback(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self.callback(event.src_path)

class FolderWatcher:
    """Watches a folder for new files"""
    
    def __init__(self, watch_path, callback):
        """
        Initialize the folder watcher
        
        Args:
            watch_path: Path to watch (string or Path)
            callback: Function to call when a file is detected
        """
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.observer = None
        self.handler = FolderWatcherHandler(callback)
        
        # Create the watch directory if it doesn't exist
        self.watch_path.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"FolderWatcher initialized for: {self.watch_path}")
    
    def start(self):
        """Start watching the folder"""
        if self.observer is None:
            self.observer = Observer()
            self.observer.schedule(self.handler, str(self.watch_path), recursive=False)
            self.observer.start()
            logging.info(f"Started watching: {self.watch_path}")
            print(f"👀 Watching: {self.watch_path}")
    
    def stop(self):
        """Stop watching the folder"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logging.info(f"Stopped watching: {self.watch_path}")
            print(f"⏹️ Stopped watching: {self.watch_path}")
    
    def is_running(self):
        """Check if the watcher is running"""
        return self.observer is not None and self.observer.is_alive()