"""
Watch Script - Monitors input folder and processes files
"""

import os
import sys
import time
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.processor import Pipeline
from src.watchers.folder_watcher import FolderWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chessbot.log'),
        logging.StreamHandler()
    ]
)

class ChessBotWatcher:
    """Main watcher class for Chess Shorts Bot"""
    
    def __init__(self, config_path="config/config.yaml"):
        self.config_path = config_path
        self.pipeline = Pipeline(config_path=config_path)
        self.watcher = None
        self.input_dir = Path("inputs/pending")
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir = Path("inputs/archive")
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*80)
        print("🚀 CHESS SHORTS BOT STARTING")
        print("="*80)
        print(f"Python version: {sys.version}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Input directory: {self.input_dir}")
        print(f"Archive directory: {self.archive_dir}")
        print("="*80 + "\n")
        
    def process_file(self, file_path):
        """Process a single file"""
        try:
            print(f"\n📁 Processing: {file_path}")
            
            # Process the file
            result = self.pipeline.process_file(file_path)
            
            if result and result.get('video'):
                video_path = result['video']
                print(f"✅ Video created: {video_path}")
                
                # Preview and confirm
                confirm = self.pipeline.brochure_processor.preview_and_confirm(video_path)
                
                if confirm:
                    # Upload the video
                    print("\n📤 Uploading video...")
                    metadata = result.get('metadata', {})
                    success = self.pipeline.upload_video(video_path, metadata)
                    
                    if success:
                        print("✅ Video uploaded successfully!")
                        # Archive the source file
                        self.archive_file(file_path)
                    else:
                        print("❌ Upload failed!")
                else:
                    print("⏭️ Upload skipped by user.")
            else:
                print(f"❌ No video created for: {file_path}")
                
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()
    
    def archive_file(self, file_path):
        """Archive the processed file"""
        try:
            file_path = Path(file_path)
            dest_path = self.archive_dir / file_path.name
            
            # Move file to archive
            shutil.move(str(file_path), str(dest_path))
            logging.info(f"Archived: {dest_path}")
            print(f"📦 Archived: {dest_path}")
            
        except Exception as e:
            logging.error(f"Error archiving {file_path}: {e}")
    
    def start(self):
        """Start watching the input directory"""
        # Set up the watcher with correct parameter names
        self.watcher = FolderWatcher(
            watch_path=str(self.input_dir),
            callback=self.process_file
        )
        
        try:
            self.watcher.start()
            print("✅ Watcher started. Press Ctrl+C to stop.")
            
            # Keep the script running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️ Stopping watcher...")
            self.watcher.stop()
            print("✅ Watcher stopped.")
        except Exception as e:
            logging.error(f"Error in watcher: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Check if config file exists
    config_path = "config/config.yaml"
    if not os.path.exists(config_path):
        print(f"⚠️ Config file not found: {config_path}")
        print("   Using default configuration.")
        config_path = None
    
    # Create and start the watcher
    watcher = ChessBotWatcher(config_path)
    watcher.start()
