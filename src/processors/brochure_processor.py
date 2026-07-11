"""
Brochure Processor - Main orchestrator module
Creates videos from chess tournament brochures and chess puzzles
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Import modules
from src.processors.modules.file_debugger import FileDebugger
from src.processors.modules.ocr_extractor import OCRExtractorModule
from src.processors.modules.metadata_generator import MetadataGenerator
from src.processors.modules.promo_manager import PromoManager
from src.processors.modules.video_creator import VideoCreator
from src.processors.modules.utils import Utils

# === CONFIGURE IMAGEMAGICK FOR MOVIEPY ===
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
os.environ["IMAGEMAGICK_BINARY"] = IMAGEMAGICK_PATH

try:
    from moviepy.config import change_settings
    change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
    print("✅ ImageMagick configured in brochure_processor")
    print(f"   Path: {IMAGEMAGICK_PATH}")
except Exception as e:
    print(f"⚠️ Could not configure ImageMagick in brochure_processor: {e}")

# Print debug at module load
print("\n" + "="*80)
print(f"🔍 LOADING BROCHURE_PROCESSOR.PY")
print(f"🔍 File location: {__file__}")
print(f"🔍 Time: {datetime.now()}")
print("="*80 + "\n")

class BrochureProcessor:
    """Main processor class that orchestrates all modules"""
    
    def __init__(self, config=None):
        self.config = config
        
        # Initialize file debugger
        self.file_debugger = FileDebugger("brochure_debug.log")
        
        # Initialize directories
        self.output_dir = Path("output/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.preview_dir = Path("output/previews")
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        
        # Define folders
        self.promotional_folder = Path(r"C:\VISWA\000000_PYTHON\0000000000JULY 2026\ChessShortsBot\inputs\pending\promotional")
        self.puzzle_folder = Path(r"C:\VISWA\000000_PYTHON\0000000000JULY 2026\ChessShortsBot\inputs\pending\brochures\Chess Puzzle")
        self.brochure_folder = Path(r"C:\VISWA\000000_PYTHON\0000000000JULY 2026\ChessShortsBot\inputs\pending\brochures")
        
        # Create folders if they don't exist
        self.promotional_folder.mkdir(parents=True, exist_ok=True)
        self.puzzle_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize modules
        self.ocr_extractor = OCRExtractorModule()
        self.metadata_generator = MetadataGenerator()
        self.promo_manager = PromoManager(self.promotional_folder)
        
        # Music path
        self.music_path = self._find_music_file()
        
        # Initialize video creator
        self.video_creator = VideoCreator(
            self.output_dir,
            self.music_path,
            self.promo_manager,
            self.file_debugger
        )
        
        # Log initialization
        self.file_debugger.log_operation("INIT", __file__, {
            "output_dir": str(self.output_dir),
            "preview_dir": str(self.preview_dir),
            "music_path": str(self.music_path) if self.music_path else "None",
            "promotional_folder": str(self.promotional_folder),
            "puzzle_folder": str(self.puzzle_folder)
        })
        
        print("\n" + "="*80)
        print("🔍 BROCHURE PROCESSOR INITIALIZED")
        print("="*80)
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📁 Preview directory: {self.preview_dir}")
        print(f"📁 Promotional folder: {self.promotional_folder}")
        print(f"📁 Puzzle folder: {self.puzzle_folder}")
        print(f"📁 Brochure folder: {self.brochure_folder}")
        print(f"🎵 Music file: {self.music_path if self.music_path else 'Not found'}")
        print(f"📁 Debug log: brochure_debug.log")
        print("="*80 + "\n")
    
    def _find_music_file(self):
        """Find music file in assets/music directory"""
        music_path = Path("assets/music/background_music.mp3")
        if not music_path.exists():
            music_dir = Path("assets/music")
            if music_dir.exists():
                music_files = list(music_dir.glob("*"))
                if music_files:
                    music_path = music_files[0]
                    print(f"🎵 Found music file: {music_path}")
                else:
                    print("⚠️ No music files found in assets/music/")
                    music_path = None
            else:
                print("⚠️ Music directory not found: assets/music/")
                music_path = None
        return music_path
    
    def print_short_details(self, info, content_type="brochure"):
        """Print the details that will be used for the YouTube Short"""
        print("\n" + "="*80)
        print(f"🎬 YOUTUBE SHORT DETAILS - {content_type.upper()}")
        print("="*80)
        
        if content_type == "puzzle":
            title = info.get('title', 'Chess Puzzle')
            description = info.get('description', 'Chess Puzzle')
        else:
            title = info.get('tournament_name', 'Not Found')
            description = f"Tournament: {title}"
        
        print("\n📌 VIDEO TITLE:")
        print("-" * 80)
        print(f"  {title}")
        print("-" * 80)
        
        print("\n📋 SHORT DESCRIPTION:")
        print("-" * 80)
        print(f"  {description}")
        print("-" * 80)
        
        print("\n📊 DETAILS USED FOR THIS SHORT:")
        print("-" * 80)
        print(f"  ✅ Title: {title}")
        print("-" * 80)
    
    def print_ocr_info(self, text, info):
        """Print OCR extracted information in a clean, formatted way"""
        print("\n" + "="*80)
        print("📋 OCR EXTRACTED INFORMATION")
        print("="*80)
        
        print("\n📄 RAW OCR TEXT (First 500 characters):")
        print("-" * 80)
        print(text[:500] + ("..." if len(text) > 500 else ""))
        print("-" * 80)
        
        print("\n📊 EXTRACTED TOURNAMENT INFORMATION:")
        print("-" * 80)
        
        fields = [
            ("🏆 Tournament Name", info.get('tournament_name', 'Not found')),
            ("📍 Venue", info.get('venue', 'Not found')),
            ("📅 Dates", ', '.join(info.get('dates', [])) or 'Not found'),
            ("💰 Entry Fee", info.get('entry_fee', 'Not found')),
            ("🏆 Prize Fund", info.get('prize_fund', 'Not found')),
            ("📞 Contact", ', '.join(info.get('contact', [])) or 'Not found'),
            ("📧 Email", ', '.join(info.get('email', [])) or 'Not found'),
            ("🌐 Website", ', '.join(info.get('website', [])) or 'Not found'),
            ("🏷️ Categories", ', '.join(info.get('categories', [])) or 'Not found')
        ]
        
        for label, value in fields:
            print(f"  {label:<20}: {value}")
        
        print("-" * 80)
    
    def print_youtube_metadata(self, title, description, hashtags):
        """Print YouTube metadata in a clean, formatted way"""
        print("\n" + "="*80)
        print("🎬 YOUTUBE METADATA GENERATED")
        print("="*80)
        
        print("\n📌 TITLE:")
        print("-" * 80)
        print(title)
        print("-" * 80)
        
        print("\n📝 DESCRIPTION:")
        print("-" * 80)
        print(description)
        print("-" * 80)
        
        print("\n#️⃣ HASHTAGS:")
        print("-" * 80)
        print(hashtags)
        print("-" * 80)
        
        print("\n📊 METADATA STATISTICS:")
        print("-" * 80)
        print(f"  Title Length     : {len(title)} characters (Max: 100)")
        print(f"  Description Length: {len(description)} characters (Max: 5000)")
        print(f"  Hashtags Length  : {len(hashtags)} characters (Max: 100)")
        print("-" * 80)
    
    def process_brochure(self, brochure_path):
        """Process a brochure image"""
        print("\n" + "="*80)
        print("🔍 PROCESSING BROCHURE")
        print("="*80)
        print(f"Input file: {brochure_path}")
        print(f"File exists: {os.path.exists(brochure_path)}")
        if os.path.exists(brochure_path):
            print(f"File size: {os.path.getsize(brochure_path)} bytes")
        print("="*80 + "\n")
        
        self.file_debugger.log_operation("PROCESS_BROCHURE_START", str(brochure_path))
        
        logging.info("=" * 70)
        logging.info("BROCHURE PROCESS STARTED")
        logging.info(f"Brochure = {brochure_path}")
        
        # Extract text using OCR
        text = self.ocr_extractor.extract_text(brochure_path)
        print(f"✅ OCR completed successfully")
        print(f"   Text length: {len(text)} characters")
        
        self.file_debugger.log_operation("OCR_COMPLETE", str(brochure_path), {
            "text_length": len(text),
            "first_100_chars": text[:100] if text else "No text"
        })
        
        # Extract tournament information
        print("\n📊 Extracting tournament information from OCR text...")
        info = self.ocr_extractor.extract_tournament_info(text)
        info["brochure"] = str(brochure_path)
        
        self.print_ocr_info(text, info)
        self.print_short_details(info, "brochure")
        
        self.file_debugger.log_operation("INFO_EXTRACTED", str(brochure_path), info)
        
        # Generate YouTube metadata
        logging.info("Generating YouTube metadata...")
        youtube_title, youtube_description, youtube_hashtags = self.metadata_generator.generate_youtube_metadata(info)
        
        self.print_youtube_metadata(youtube_title, youtube_description, youtube_hashtags)
        
        info['youtube_title'] = youtube_title
        info['youtube_description'] = youtube_description
        info['youtube_hashtags'] = youtube_hashtags
        
        # Create video
        logging.info("Creating video from brochure...")
        print("\n🎬 GENERATING VIDEO...")
        print(f"Using brochure: {brochure_path}")
        
        video_path = self.video_creator.create_video_with_promotion(brochure_path, info, "brochure")
        
        if video_path and os.path.exists(video_path):
            print(f"✅ Video created: {video_path}")
            print(f"📊 Video size: {os.path.getsize(video_path)} bytes")
            self.file_debugger.log_operation("VIDEO_CREATED", str(video_path), {
                "source": str(brochure_path),
                "size": os.path.getsize(video_path)
            })
        else:
            print("❌ Video creation failed!")
            self.file_debugger.log_operation("VIDEO_CREATION_FAILED", str(video_path))
        
        logging.info(f"Video created: {video_path}")
        
        return video_path, info
    
    def process_puzzle(self, puzzle_path):
        """Process a chess puzzle image"""
        print("\n" + "="*80)
        print("🔍 PROCESSING CHESS PUZZLE")
        print("="*80)
        print(f"Input file: {puzzle_path}")
        print(f"File exists: {os.path.exists(puzzle_path)}")
        if os.path.exists(puzzle_path):
            print(f"File size: {os.path.getsize(puzzle_path)} bytes")
        print("="*80 + "\n")
        
        self.file_debugger.log_operation("PROCESS_PUZZLE_START", str(puzzle_path))
        
        file_name = Path(puzzle_path).stem
        
        info = {
            "puzzle_path": str(puzzle_path),
            "title": f"Chess Puzzle - {file_name}",
            "description": f"Chess Puzzle: {file_name}. Test your chess skills with this puzzle!",
            "file_name": file_name
        }
        
        self.print_short_details(info, "puzzle")
        
        youtube_title = f"Chess Puzzle - {file_name}"
        youtube_description = f"♟️ Chess Puzzle: {file_name}\n\nTest your chess skills with this puzzle!\n\n🔹 Can you find the best move?\n🔹 Challenge yourself!\n🔹 Improve your chess tactics!\n\n#Chess #ChessPuzzle #ChessTactics #ChessTraining"
        youtube_hashtags = "#Chess #ChessPuzzle #ChessTactics #ChessTraining #ChessLife #ChessGame"
        
        info['youtube_title'] = youtube_title
        info['youtube_description'] = youtube_description
        info['youtube_hashtags'] = youtube_hashtags
        
        self.print_youtube_metadata(youtube_title, youtube_description, youtube_hashtags)
        
        print("\n🎬 GENERATING VIDEO...")
        print(f"Using puzzle: {puzzle_path}")
        
        video_path = self.video_creator.create_video_with_promotion(puzzle_path, info, "puzzle")
        
        if video_path and os.path.exists(video_path):
            print(f"✅ Video created: {video_path}")
            print(f"📊 Video size: {os.path.getsize(video_path)} bytes")
            self.file_debugger.log_operation("VIDEO_CREATED", str(video_path), {
                "source": str(puzzle_path),
                "size": os.path.getsize(video_path)
            })
        else:
            print("❌ Video creation failed!")
            self.file_debugger.log_operation("VIDEO_CREATION_FAILED", str(video_path))
        
        return video_path, info
    
    # ============ COMPATIBILITY WRAPPER METHODS ============
    
    def create_brochure_video(self, brochure_path):
        """COMPATIBILITY WRAPPER: Creates a video from brochure (legacy method name)"""
        print("\n🔄 Compatibility wrapper: create_brochure_video() called")
        print(f"   Processing: {brochure_path}")
        
        if str(Path(brochure_path).parent).lower() == str(self.puzzle_folder).lower():
            video_path, info = self.process_puzzle(brochure_path)
        else:
            video_path, info = self.process_brochure(brochure_path)
        
        return video_path
    
    def process(self, file_path):
        """Main processing method - called by the watcher"""
        file_path = Path(file_path)
        
        if str(file_path.parent).lower() == str(self.puzzle_folder).lower():
            video_path, info = self.process_puzzle(file_path)
        else:
            video_path, info = self.process_brochure(file_path)
        
        return {
            "video": video_path,
            "thumbnail": None,
            "metadata": info,
            "skipped": False
        }
    
    def preview_and_confirm(self, video_path):
        """Preview the video and ask user for confirmation"""
        print("\n" + "="*80)
        print("👀 VIDEO PREVIEW & CONFIRMATION")
        print("="*80)
        
        if not video_path or not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            print(f"❌ Video file not found: {video_path}")
            self.file_debugger.log_operation("PREVIEW_ERROR", str(video_path), {"error": "File not found"})
            return False
        
        video_size = os.path.getsize(video_path)
        print(f"📹 Video file: {video_path}")
        print(f"📊 Video size: {video_size:,} bytes ({video_size/1024/1024:.2f} MB)")
        
        if video_size < 1000:
            logging.error(f"Video file too small ({video_size} bytes), likely corrupted")
            print(f"❌ Video file too small ({video_size} bytes), likely corrupted!")
            self.file_debugger.log_operation("PREVIEW_ERROR", str(video_path), {"error": "File too small"})
            return False
        
        print("\n🎬 The video will now open for preview...")
        print("⏱️ Video duration: ~25 seconds (with background music)")
        print("🎵 Includes promotional end card for online classes")
        
        Utils.preview_video(video_path)
        
        print("\n" + "-"*70)
        print("📋 VIDEO PREVIEW OPTIONS:")
        print("  y = Yes, upload this video")
        print("  n = No, skip upload")
        print("  v = View video again")
        print("  l = Show debug log")
        print("-"*70)
        
        while True:
            choice = input("❓ Upload this video? (y/n/v/l): ").lower().strip()
            
            if choice == 'y':
                print("✅ Upload confirmed!")
                self.file_debugger.log_operation("UPLOAD_CONFIRMED", str(video_path))
                return True
            elif choice == 'n':
                print("⏭️ Upload skipped.")
                self.file_debugger.log_operation("UPLOAD_SKIPPED", str(video_path))
                return False
            elif choice == 'v':
                Utils.preview_video(video_path)
            elif choice == 'l':
                try:
                    with open("brochure_debug.log", 'r') as f:
                        log_content = f.read()
                        print("\n" + "="*80)
                        print("📋 DEBUG LOG (last 50 lines):")
                        print("="*80)
                        lines = log_content.splitlines()
                        for line in lines[-50:]:
                            print(line)
                        print("="*80 + "\n")
                except:
                    print("Could not read debug log.")
            else:
                print("Please enter: 'y' (yes), 'n' (no), 'v' (view again), or 'l' (show log)")
    
    def create_promotion_slide(self):
        """Create end promotion for online classes"""
        return "Join Online Chess Classes - akhil.chess3@gmail.com"