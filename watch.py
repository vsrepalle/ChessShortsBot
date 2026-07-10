#!/usr/bin/env python
# === CONFIGURE IMAGEMAGICK FOR MOVIEPY ===
import os
import sys
import time
from pathlib import Path

# Configure ImageMagick path for MoviePy
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
os.environ["IMAGEMAGICK_BINARY"] = IMAGEMAGICK_PATH

# Configure moviepy
try:
    from moviepy.config import change_settings
    change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
    print("✅ ImageMagick configured successfully")
    print(f"   Path: {IMAGEMAGICK_PATH}")
except Exception as e:
    print(f"⚠️ Could not configure ImageMagick: {e}")
    print(f"   Please check if ImageMagick is installed at: {IMAGEMAGICK_PATH}")

# Now import the rest
from src.core.processor import Pipeline
from src.watchers.folder_watcher import watch

# Print startup info
print("\n" + "="*80)
print("🚀 CHESS SHORTS BOT STARTING")
print("="*80)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Check if the processor file exists
processor_file = Path("src/processors/brochure_processor.py")
if processor_file.exists():
    print(f"✅ Processor file exists: {processor_file}")
    print(f"   Size: {processor_file.stat().st_size} bytes")
    print(f"   Modified: {time.ctime(processor_file.stat().st_mtime)}")
    
    # Check if it has the new methods (using UTF-8 encoding)
    try:
        with open(processor_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'preview_and_confirm' in content:
                print("   ✅ Has preview_and_confirm method (NEW CODE)")
            else:
                print("   ❌ MISSING preview_and_confirm method (OLD CODE)")
            
            if 'create_brochure_video' in content:
                print("   ✅ Has create_brochure_video method (NEW CODE)")
            else:
                print("   ❌ MISSING create_brochure_video method (OLD CODE)")
    except Exception as e:
        print(f"   ⚠️ Could not read file: {e}")
else:
    print(f"❌ Processor file NOT FOUND at: {processor_file}")

print("="*80 + "\n")

pipeline = Pipeline(
    config_path="config/config.yaml"
)

def process_file(path):
    ext = os.path.splitext(path)[1].lower()
    
    print(f"Detected : {path}")
    
    # Check if file still exists before processing
    if not os.path.exists(path):
        print(f"⚠️ File no longer exists: {path}")
        return
    
    if ext == ".pgn":
        print("Processing PGN")
        class FileInfo:
            def __init__(self, path):
                self.name = os.path.basename(path)
                self.suffix = ".pgn"
        
        pipeline.process_pgn(FileInfo(path))
    
    elif ext in [".pdf", ".jpg", ".jpeg", ".png"]:
        print("Processing Brochure")
        
        # Force reload before processing
        import importlib
        if 'src.processors.brochure_processor' in sys.modules:
            del sys.modules['src.processors.brochure_processor']
            print("🔄 Reloaded brochure processor module")
        
        from src.processors.brochure_processor import BrochureProcessor
        print(f"📁 Using processor from: {BrochureProcessor.__module__}")
        
        # Check if file still exists
        if not os.path.exists(path):
            print(f"⚠️ File no longer exists: {path}")
            return
        
        # Process directly
        processor = BrochureProcessor(pipeline.config)
        result = processor.process(path)
        
        if result and not result.get('skipped', False):
            video_file = result.get("video")
            if video_file and os.path.exists(video_file):
                print(f"📤 Uploading video: {video_file}")
                try:
                    pipeline.youtube.upload(
                        video_file=video_file,
                        metadata=result.get('metadata', {}),
                        thumbnail=result.get('thumbnail')
                    )
                    # Only archive if file still exists
                    if os.path.exists(path):
                        pipeline.archive_file(path)
                except Exception as e:
                    print(f"❌ Upload failed: {e}")
            else:
                print("❌ No video to upload")
                if os.path.exists(path):
                    pipeline.archive_file(path)
        else:
            print("⏭️ Upload skipped")
            if os.path.exists(path):
                pipeline.archive_file(path)
    
    else:
        print("Unsupported File")

watch(
    "inputs/pending",
    process_file
)
