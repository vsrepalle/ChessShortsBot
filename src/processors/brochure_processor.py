"""
Brochure Processor - Creates videos from chess tournament brochures
Shows the brochure as-is in the video with background music and promotional end card
"""

import os
import shutil
import logging
import re
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from src.ocr.extractor import OCRExtractor
from moviepy.editor import (
    ImageClip, 
    CompositeVideoClip, 
    TextClip, 
    ColorClip,
    VideoFileClip,
    concatenate_videoclips,
    AudioFileClip,
    CompositeAudioClip
)
from moviepy.video.fx.all import fadein, fadeout
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
import subprocess
import sys
import json
import hashlib

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

# File debugger class
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
    
    def log_operation(self, operation, file_path, details=None):
        """Log a file operation with timestamp and details"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "file": str(file_path) if file_path else "None",
            "details": details or {},
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
            if details:
                f.write(f"  Details: {json.dumps(details, indent=2)}\n")
            f.write("-" * 80 + "\n")
    
    def get_file_hash(self, file_path):
        """Get file hash for verification"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
        except:
            return None
        return None

# Global debugger instance
file_debugger = FileDebugger("brochure_debug.log")

class BrochureProcessor:
    def __init__(self, config=None):
        self.config = config
        self.ocr = OCRExtractor()
        self.output_dir = Path("output/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.preview_dir = Path("output/previews")
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        
        # Music path - update this to your actual music file
        self.music_path = Path("assets/music/background_music.mp3")
        if not self.music_path.exists():
            # Try common music file extensions
            music_dir = Path("assets/music")
            if music_dir.exists():
                music_files = list(music_dir.glob("*"))
                if music_files:
                    self.music_path = music_files[0]
                    print(f"🎵 Found music file: {self.music_path}")
                else:
                    print("⚠️ No music files found in assets/music/")
                    self.music_path = None
            else:
                print("⚠️ Music directory not found: assets/music/")
                self.music_path = None
        
        # Log initialization
        file_debugger.log_operation("INIT", __file__, {
            "output_dir": str(self.output_dir),
            "preview_dir": str(self.preview_dir),
            "music_path": str(self.music_path) if self.music_path else "None"
        })
        
        print("\n" + "="*80)
        print("🔍 BROCHURE PROCESSOR INITIALIZED")
        print("="*80)
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📁 Preview directory: {self.preview_dir}")
        print(f"🎵 Music file: {self.music_path if self.music_path else 'Not found'}")
        print(f"📁 Debug log: brochure_debug.log")
        print("="*80 + "\n")

    def process(self, brochure_path):
        print("\n" + "="*80)
        print("🔍 PROCESSING BROCHURE")
        print("="*80)
        print(f"Input file: {brochure_path}")
        print(f"File exists: {os.path.exists(brochure_path)}")
        if os.path.exists(brochure_path):
            print(f"File size: {os.path.getsize(brochure_path)} bytes")
        print("="*80 + "\n")
        
        file_debugger.log_operation("PROCESS_START", brochure_path)
        
        logging.info("=" * 70)
        logging.info("BROCHURE PROCESS STARTED")
        logging.info(f"Brochure = {brochure_path}")

        # Step 1: Extract text from brochure (for metadata only)
        logging.info("Calling OCRExtractor.extract()")
        try:
            text = self.ocr.extract(brochure_path)
        except Exception as e:
            logging.error(f"OCR failed: {e}")
            text = "Chess Tournament Brochure"
        
        logging.info("OCR completed")
        logging.info(f"OCR Text Length = {len(text)}")
        
        file_debugger.log_operation("OCR_COMPLETE", brochure_path, {
            "text_length": len(text),
            "first_100_chars": text[:100] if text else "No text"
        })

        # Step 2: Extract tournament information (for metadata only)
        logging.info("Extracting tournament information")
        info = {
            "brochure": brochure_path,
            "raw_text": text,
            "tournament_name": self.find_tournament(text) or "Chess Tournament",
            "venue": self.find_venue(text) or "",
            "dates": self.find_dates(text) or [],
            "entry_fee": self.find_entry_fee(text) or "",
            "prize_fund": self.find_prize(text) or "",
            "contact": self.find_contact(text) or [],
            "email": self.find_email(text) or [],
            "website": self.find_website(text) or [],
            "categories": self.find_categories(text) or []
        }
        logging.info("Brochure processing finished")
        logging.info(info)
        
        file_debugger.log_operation("INFO_EXTRACTED", brochure_path, info)

        # Step 3: Create video from brochure (SHOW AS-IS with music and promo)
        logging.info("Creating video from brochure...")
        print("\n🎬 GENERATING VIDEO...")
        print(f"Using brochure: {brochure_path}")
        
        video_path = self.create_brochure_video_with_music(brochure_path, info)
        
        if video_path and os.path.exists(video_path):
            print(f"✅ Video created: {video_path}")
            print(f"📊 Video size: {os.path.getsize(video_path)} bytes")
            file_debugger.log_operation("VIDEO_CREATED", video_path, {
                "source": brochure_path,
                "size": os.path.getsize(video_path)
            })
        else:
            print("❌ Video creation failed!")
            file_debugger.log_operation("VIDEO_CREATION_FAILED", video_path)
        
        logging.info(f"Video created: {video_path}")
        
        # Step 4: Preview video and ask for confirmation
        print("\n👀 PREVIEW AND CONFIRM...")
        confirm = self.preview_and_confirm(video_path)
        file_debugger.log_operation("USER_CONFIRMATION", video_path, {
            "confirmed": confirm
        })
        
        if not confirm:
            logging.info("User chose to skip upload")
            print("⏭️ User skipped upload")
            return {
                "video": None,
                "thumbnail": None,
                "metadata": info,
                "skipped": True
            }
        
        # Step 5: Return result for pipeline
        print("✅ Upload confirmed by user")
        return {
            "video": video_path,
            "thumbnail": None,
            "metadata": {
                "Title": Path(brochure_path).stem,
                "Tournament": info['tournament_name'],
                "Venue": info['venue'],
                "Dates": ', '.join(info['dates']) if info['dates'] else ''
            },
            "skipped": False
        }

    def create_promotional_end_card(self, duration=5, info=None):
        """
        Create a promotional end card for online chess classes
        """
        # Create a colored background
        bg = ColorClip(size=(1080, 1920), color=(20, 20, 30), duration=duration)
        
        # Create promo text
        promo_texts = []
        
        # Main title
        title = TextClip(
            "♟️ ONLINE CHESS CLASSES",
            fontsize=80,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=2,
            size=(900, None)
        ).set_position(('center', 400))
        
        # Subtitle
        subtitle = TextClip(
            "Learn from Expert Coaches",
            fontsize=50,
            color='gold',
            font='Arial',
            size=(800, None)
        ).set_position(('center', 550))
        
        # Contact info - ONLY EMAIL (removed phone)
        contact_text = "📧 akhil.chess3@gmail.com"
        if info and info.get('email'):
            email = info['email'][0] if info['email'] else 'akhil.chess3@gmail.com'
            contact_text = f"📧 {email}"
        
        contact = TextClip(
            contact_text,
            fontsize=45,
            color='lightblue',
            font='Arial',
            method='label',
            size=(800, None)
        ).set_position(('center', 750))
        
        # Features
        features = TextClip(
            "• All Levels Welcome\n• Individual Attention\n• Flexible Timings\n• Tournament Preparation",
            fontsize=40,
            color='white',
            font='Arial',
            method='label',
            size=(800, None)
        ).set_position(('center', 1050))
        
        # Call to action - WITHOUT phone number
        cta = TextClip(
            "📧 Contact us for more details",
            fontsize=45,
            color='#FFD700',
            font='Arial-Bold',
            method='label'
        ).set_position(('center', 1650))
        
        # Removed website and phone number sections
        
        # Compose the end card
        end_card = CompositeVideoClip([bg, title, subtitle, contact, features, cta])
        end_card = end_card.set_duration(duration)
        
        # Add fade effects
        end_card = fadein(end_card, 0.5)
        end_card = fadeout(end_card, 0.5)
        
        return end_card

    def create_brochure_video_with_music(self, brochure_path, info=None):
        """
        Create a video showing the brochure as-is with background music and promotional end card
        """
        print("\n" + "="*80)
        print("🎬 CREATING VIDEO WITH MUSIC AND PROMO")
        print("="*80)
        print(f"Source image: {brochure_path}")
        print(f"File exists: {os.path.exists(brochure_path)}")
        if os.path.exists(brochure_path):
            print(f"File size: {os.path.getsize(brochure_path)} bytes")
        print("="*80 + "\n")
        
        file_debugger.log_operation("VIDEO_CREATE_START", brochure_path)
        
        try:
            # Check if image exists
            if not os.path.exists(brochure_path):
                logging.error(f"Image file not found: {brochure_path}")
                print(f"❌ ERROR: Image file not found: {brochure_path}")
                file_debugger.log_operation("ERROR", brochure_path, {"error": "File not found"})
                return None
            
            # Try to load with OpenCV first for debugging
            print("📸 Loading image with OpenCV...")
            img_cv = cv2.imread(brochure_path)
            if img_cv is None:
                logging.error(f"OpenCV could not load image: {brochure_path}")
                print(f"❌ ERROR: OpenCV could not load image: {brochure_path}")
                file_debugger.log_operation("ERROR", brochure_path, {"error": "OpenCV load failed"})
                return None
            
            print(f"✅ OpenCV loaded image successfully")
            print(f"  Shape: {img_cv.shape}")
            print(f"  Type: {img_cv.dtype}")
            
            # Save a debug copy
            debug_filename = f"debug_{Path(brochure_path).stem}_{datetime.now().strftime('%H%M%S')}.jpg"
            debug_path = self.preview_dir / debug_filename
            cv2.imwrite(str(debug_path), img_cv)
            print(f"📸 Debug image saved: {debug_path}")
            print(f"  Debug file size: {os.path.getsize(debug_path)} bytes")
            
            file_debugger.log_operation("DEBUG_IMAGE_SAVED", debug_path, {
                "source": brochure_path,
                "size": os.path.getsize(debug_path)
            })
            
            # Set video duration
            brochure_duration = 20  # Show brochure for 20 seconds
            promo_duration = 5      # Show promo for 5 seconds
            total_duration = brochure_duration + promo_duration
            
            # Load with moviepy
            print("🎥 Loading with MoviePy...")
            brochure_clip = ImageClip(brochure_path)
            print(f"✅ MoviePy loaded clip")
            print(f"  Original size: {brochure_clip.size}")
            
            file_debugger.log_operation("MOVIEPY_LOADED", brochure_path, {
                "size": brochure_clip.size
            })
            
            # Get dimensions
            target_width = 1080
            target_height = 1920
            
            print(f"🎯 Target dimensions: {target_width}x{target_height}")
            
            # Determine if we need to resize or add background
            original_width, original_height = brochure_clip.size
            
            # Calculate aspect ratios
            original_aspect = original_width / original_height
            target_aspect = target_width / target_height
            
            print(f"  Original aspect: {original_aspect:.2f}")
            print(f"  Target aspect: {target_aspect:.2f}")
            
            # Create brochure clip
            if original_aspect > target_aspect:
                # Image is wider than target - resize to fit width, add black bars top/bottom
                print("  Image is wider - resizing to fit width")
                brochure_clip = brochure_clip.resize(width=target_width)
                # Center vertically
                y_pos = (target_height - brochure_clip.h) // 2
                brochure_clip = brochure_clip.set_position(('center', y_pos))
                
                # Add black background with duration
                bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
                bg = bg.set_duration(brochure_duration)
                brochure_clip = CompositeVideoClip([bg, brochure_clip])
                brochure_clip = brochure_clip.set_duration(brochure_duration)
                
            else:
                # Image is taller or equal - resize to fit height, add black bars left/right
                print("  Image is taller - resizing to fit height")
                brochure_clip = brochure_clip.resize(height=target_height)
                # Center horizontally
                x_pos = (target_width - brochure_clip.w) // 2
                brochure_clip = brochure_clip.set_position((x_pos, 'center'))
                
                # Add black background with duration
                bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
                bg = bg.set_duration(brochure_duration)
                brochure_clip = CompositeVideoClip([bg, brochure_clip])
                brochure_clip = brochure_clip.set_duration(brochure_duration)
            
            print(f"✅ Brochure clip created")
            print(f"  Size: {brochure_clip.size}")
            print(f"  Duration: {brochure_clip.duration} seconds")
            
            # Create promotional end card
            print("🎨 Creating promotional end card...")
            end_card = self.create_promotional_end_card(promo_duration, info)
            
            # Combine both clips
            print("🔗 Combining clips...")
            final_clip = concatenate_videoclips([brochure_clip, end_card])
            
            # Add fade effects to the entire video
            final_clip = fadein(final_clip, 0.5)
            final_clip = fadeout(final_clip, 0.5)
            
            print(f"✅ Final clip created")
            print(f"  Final size: {final_clip.size}")
            print(f"  Total duration: {final_clip.duration} seconds")
            
            # Load and add background music
            print("🎵 Loading background music...")
            audio_clip = None
            if self.music_path and self.music_path.exists():
                try:
                    audio_clip = AudioFileClip(str(self.music_path))
                    # Trim or loop audio to match video duration
                    if audio_clip.duration < total_duration:
                        # Loop audio if it's shorter than video
                        audio_clip = audio_clip.loop(duration=total_duration)
                    else:
                        # Trim audio if it's longer than video
                        audio_clip = audio_clip.subclip(0, total_duration)
                    
                    # Add fade effects to audio
                    audio_clip = audio_fadein(audio_clip, 0.5)
                    audio_clip = audio_fadeout(audio_clip, 1.0)
                    
                    # Reduce volume to 70% so it doesn't overpower
                    audio_clip = audio_clip.volumex(0.7)
                    
                    print(f"✅ Audio loaded successfully")
                    print(f"  Audio duration: {audio_clip.duration} seconds")
                    print(f"  Audio file: {self.music_path}")
                    
                    # Set audio to final clip
                    final_clip = final_clip.set_audio(audio_clip)
                except Exception as e:
                    print(f"⚠️ Could not load audio: {e}")
                    print("  Continuing without music...")
            else:
                print("⚠️ No music file available - skipping audio")
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"brochure_{Path(brochure_path).stem}_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            print(f"💾 Saving video to: {output_path}")
            
            # Write the video file
            print("⏳ Rendering video (this may take a moment)...")
            final_clip.write_videofile(
                str(output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                verbose=False,
                logger=None
            )
            print("✅ Video rendering complete")
            
            # Verify video was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size = os.path.getsize(output_path)
                print(f"✅ Video created successfully")
                print(f"  Location: {output_path}")
                print(f"  Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                print(f"  Duration: {total_duration} seconds")
                
                file_debugger.log_operation("VIDEO_SAVED", output_path, {
                    "source": brochure_path,
                    "size": file_size,
                    "duration": total_duration,
                    "music": str(self.music_path) if self.music_path else "None"
                })
            else:
                logging.error("Video file is empty or missing")
                print("❌ ERROR: Video file is empty or missing!")
                file_debugger.log_operation("ERROR", output_path, {"error": "Empty or missing video"})
                return None
            
            # Clean up
            final_clip.close()
            if audio_clip:
                audio_clip.close()
            
            # Final debug summary
            print("\n" + "="*80)
            print("📊 VIDEO CREATION SUMMARY")
            print("="*80)
            print(f"📸 Source image: {brochure_path} (exists: {os.path.exists(brochure_path)})")
            print(f"📸 Debug image: {debug_path} (size: {os.path.getsize(debug_path)} bytes)")
            print(f"🎬 Video output: {output_path} (size: {os.path.getsize(output_path)} bytes)")
            print(f"⏱️ Video duration: {total_duration} seconds")
            print(f"🎵 Background music: {self.music_path if self.music_path else 'None'}")
            print(f"📋 Debug log: brochure_debug.log")
            print("="*80 + "\n")
            
            return str(output_path)
            
        except Exception as e:
            logging.error(f"Error creating video: {e}")
            print(f"❌ ERROR creating video: {e}")
            import traceback
            traceback.print_exc()
            
            file_debugger.log_operation("ERROR", brochure_path, {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            return None

    def preview_and_confirm(self, video_path):
        """
        Preview the video and ask user for confirmation
        Returns True if user wants to upload, False otherwise
        """
        print("\n" + "="*80)
        print("👀 VIDEO PREVIEW & CONFIRMATION")
        print("="*80)
        
        if not video_path or not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            print(f"❌ Video file not found: {video_path}")
            file_debugger.log_operation("PREVIEW_ERROR", video_path, {"error": "File not found"})
            return False
        
        video_size = os.path.getsize(video_path)
        print(f"📹 Video file: {video_path}")
        print(f"📊 Video size: {video_size:,} bytes ({video_size/1024/1024:.2f} MB)")
        
        if video_size < 1000:  # Less than 1KB - likely corrupted
            logging.error(f"Video file too small ({video_size} bytes), likely corrupted")
            print(f"❌ Video file too small ({video_size} bytes), likely corrupted!")
            file_debugger.log_operation("PREVIEW_ERROR", video_path, {"error": "File too small"})
            return False
        
        print("\n🎬 The video will now open for preview...")
        print("⏱️ Video duration: ~25 seconds (with background music)")
        print("🎵 Includes promotional end card for online classes")
        
        # Try to open the video with default player
        try:
            if sys.platform == 'win32':
                os.startfile(video_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', video_path])
            else:  # Linux
                subprocess.run(['xdg-open', video_path])
            print("✅ Video player opened.")
        except Exception as e:
            print(f"⚠️ Could not auto-open video: {e}")
            print(f"Please manually open: {video_path}")
        
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
                file_debugger.log_operation("UPLOAD_CONFIRMED", video_path)
                return True
            elif choice == 'n':
                print("⏭️ Upload skipped.")
                file_debugger.log_operation("UPLOAD_SKIPPED", video_path)
                return False
            elif choice == 'v':
                try:
                    if sys.platform == 'win32':
                        os.startfile(video_path)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', video_path])
                    else:
                        subprocess.run(['xdg-open', video_path])
                    print("✅ Video opened again.")
                except:
                    print(f"Please manually open: {video_path}")
            elif choice == 'l':
                # Show the debug log
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

    # All extraction methods
    def find_tournament(self, text):
        lines = text.splitlines()
        for line in lines:
            if "CHESS" in line.upper():
                return line.strip()
        return ""

    def find_dates(self, text):
        pattern = r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        return re.findall(pattern, text)

    def find_contact(self, text):
        pattern = r"(?:\+91[- ]?)?[6-9]\d{9}"
        return re.findall(pattern, text)

    def find_email(self, text):
        pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        return re.findall(pattern, text)

    def find_website(self, text):
        pattern = r"(https?://\S+|www\.\S+)"
        return re.findall(pattern, text)

    def find_entry_fee(self, text):
        # Fixed regex - removed the problematic ?? quantifier
        pattern = r"(?:Entry Fee|Registration Fee|Fee)\D{0,10}\s?([\d,]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else ""

    def find_prize(self, text):
        # Fixed regex - removed the problematic ?? quantifier
        pattern = r"(?:Prize Fund|Total Prize|Prize)\D{0,10}\s?([\d,]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else ""

    def find_categories(self, text):
        categories = []
        possible = ["U7","U9","U11","U13","U15","U17","U19","Open","Women"]
        upper = text.upper()
        for cat in possible:
            if cat in upper:
                categories.append(cat)
        return categories

    def find_venue(self, text):
        """Find venue from text."""
        keywords = ["VENUE", "LOCATION", "ADDRESS", "AT", "PLACE"]
        lines = text.split("\n")
        for i, line in enumerate(lines):
            for key in keywords:
                if key in line.upper():
                    if i + 1 < len(lines):
                        return lines[i + 1].strip()
        return "Online Classes Available"

    def generate_youtube_metadata(self, text):
        """Generate YouTube title, description, hashtags from OCR"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        title = (lines[0][:80] if lines else "Chess Training & Masterclass")
        description = "Expert chess classes for all levels. Improve your tactics, strategy and gameplay.\n\n" + "\n".join(lines[:10])
        hashtags = "#Chess #ChessClasses #OnlineChess #ChessTraining #ChessCoach #ImproveYourChess"
        
        return title, description, hashtags

    def create_promotion_slide(self):
        """Create end promotion for online classes"""
        # This can be enhanced with PIL to create image
        return "Join Online Chess Classes - akhil.chess3@gmail.com"