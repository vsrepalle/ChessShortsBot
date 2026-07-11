"""
Video Creator Module - Handles video creation from images
"""

import os
import cv2
import logging
from pathlib import Path
from datetime import datetime
from moviepy.editor import (
    ImageClip, CompositeVideoClip, TextClip, ColorClip,
    concatenate_videoclips, AudioFileClip
)
from moviepy.video.fx.all import fadein, fadeout
from moviepy.audio.fx.all import audio_fadein, audio_fadeout

class VideoCreator:
    """Handles video creation from images with promotional content"""
    
    def __init__(self, output_dir, music_path, promo_manager, file_debugger):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.music_path = music_path
        self.promo_manager = promo_manager
        self.file_debugger = file_debugger
    
    def create_video_with_promotion(self, image_path, info, content_type="brochure"):
        """Create a video showing the image with promotional end card"""
        print("\n" + "="*80)
        print(f"🎬 CREATING VIDEO WITH PROMOTION ({content_type.upper()})")
        print("="*80)
        print(f"Source image: {image_path}")
        print(f"File exists: {os.path.exists(image_path)}")
        if os.path.exists(image_path):
            print(f"File size: {os.path.getsize(image_path)} bytes")
        print("="*80 + "\n")
        
        self.file_debugger.log_operation("VIDEO_CREATE_START", str(image_path))
        
        try:
            if not os.path.exists(image_path):
                logging.error(f"Image file not found: {image_path}")
                print(f"❌ ERROR: Image file not found: {image_path}")
                self.file_debugger.log_operation("ERROR", str(image_path), {"error": "File not found"})
                return None
            
            # Convert to string if it's a Path object
            image_path_str = str(image_path)
            
            # Load and resize image
            main_clip = self._load_and_resize_image(image_path_str, "main")
            
            # Add overlay if puzzle
            if content_type == "puzzle":
                overlay_text = info.get('title', 'Chess Puzzle')
                main_clip = self._add_overlay(main_clip, overlay_text)
            
            print(f"✅ Main clip created")
            print(f"  Size: {main_clip.size}")
            print(f"  Duration: {main_clip.duration} seconds")
            
            # Get promotional clip
            print("📸 Loading promotional clip...")
            promo_clip = self.promo_manager.get_promotional_clip(5, info)
            
            # Combine clips
            print("🔗 Combining clips...")
            final_clip = concatenate_videoclips([main_clip, promo_clip])
            
            # Add fade effects
            final_clip = fadein(final_clip, 0.5)
            final_clip = fadeout(final_clip, 0.5)
            
            print(f"✅ Final clip created")
            print(f"  Final size: {final_clip.size}")
            print(f"  Total duration: {final_clip.duration} seconds")
            
            # Add background music
            final_clip = self._add_audio(final_clip)
            
            # Save video
            output_path = self._save_video(final_clip, image_path_str, content_type)
            
            # Clean up
            final_clip.close()
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error creating video: {e}")
            print(f"❌ ERROR creating video: {e}")
            import traceback
            traceback.print_exc()
            
            self.file_debugger.log_operation("ERROR", str(image_path), {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            return None
    
    def _load_and_resize_image(self, image_path, clip_type="main"):
        """Load and resize image to fit target dimensions"""
        print("📸 Loading image with OpenCV...")
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            raise ValueError(f"OpenCV could not load image: {image_path}")
        
        print(f"✅ OpenCV loaded image successfully")
        print(f"  Shape: {img_cv.shape}")
        print(f"  Type: {img_cv.dtype}")
        
        duration = 20 if clip_type == "main" else 5
        
        print("🎥 Loading with MoviePy...")
        # Ensure image_path is a string
        clip = ImageClip(str(image_path))
        print(f"✅ MoviePy loaded clip")
        print(f"  Original size: {clip.size}")
        
        target_width = 1080
        target_height = 1920
        
        print(f"🎯 Target dimensions: {target_width}x{target_height}")
        
        original_width, original_height = clip.size
        original_aspect = original_width / original_height
        target_aspect = target_width / target_height
        
        print(f"  Original aspect: {original_aspect:.2f}")
        print(f"  Target aspect: {target_aspect:.2f}")
        
        if original_aspect > target_aspect:
            print("  Image is wider - resizing to fit width")
            clip = clip.resize(width=target_width)
            y_pos = (target_height - clip.h) // 2
            clip = clip.set_position(('center', y_pos))
            
            bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
            bg = bg.set_duration(duration)
            clip = CompositeVideoClip([bg, clip])
            clip = clip.set_duration(duration)
        else:
            print("  Image is taller - resizing to fit height")
            clip = clip.resize(height=target_height)
            x_pos = (target_width - clip.w) // 2
            clip = clip.set_position((x_pos, 'center'))
            
            bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
            bg = bg.set_duration(duration)
            clip = CompositeVideoClip([bg, clip])
            clip = clip.set_duration(duration)
        
        return clip
    
    def _add_overlay(self, clip, overlay_text):
        """Add text overlay on the video"""
        if not overlay_text:
            return clip
        
        text_clip = TextClip(
            overlay_text,
            fontsize=50,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=3,
            method='label',
            size=(900, None)
        ).set_position(('center', 50)).set_duration(clip.duration)
        
        return CompositeVideoClip([clip, text_clip])
    
    def _add_audio(self, clip):
        """Add background music to the video"""
        print("🎵 Loading background music...")
        
        if self.music_path and self.music_path.exists():
            try:
                audio_clip = AudioFileClip(str(self.music_path))
                total_duration = clip.duration
                
                if audio_clip.duration < total_duration:
                    audio_clip = audio_clip.loop(duration=total_duration)
                else:
                    audio_clip = audio_clip.subclip(0, total_duration)
                
                audio_clip = audio_fadein(audio_clip, 0.5)
                audio_clip = audio_fadeout(audio_clip, 1.0)
                audio_clip = audio_clip.volumex(0.7)
                
                print(f"✅ Audio loaded successfully")
                print(f"  Audio duration: {audio_clip.duration} seconds")
                print(f"  Audio file: {self.music_path}")
                
                clip = clip.set_audio(audio_clip)
            except Exception as e:
                print(f"⚠️ Could not load audio: {e}")
                print("  Continuing without music...")
        else:
            print("⚠️ No music file available - skipping audio")
        
        return clip
    
    def _save_video(self, clip, image_path, content_type):
        """Save the video to output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = Path(image_path).stem
        output_filename = f"{content_type}_{file_name}_{timestamp}.mp4"
        output_path = self.output_dir / output_filename
        
        print(f"💾 Saving video to: {output_path}")
        print("⏳ Rendering video (this may take a moment)...")
        
        clip.write_videofile(
            str(output_path),
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            verbose=False,
            logger=None
        )
        print("✅ Video rendering complete")
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size = os.path.getsize(output_path)
            print(f"✅ Video created successfully")
            print(f"  Location: {output_path}")
            print(f"  Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            print(f"  Duration: {clip.duration} seconds")
            
            self.file_debugger.log_operation("VIDEO_SAVED", str(output_path), {
                "source": str(image_path),
                "size": file_size,
                "duration": clip.duration,
                "music": str(self.music_path) if self.music_path else "None"
            })
            
            return str(output_path)
        else:
            raise ValueError("Video file is empty or missing")