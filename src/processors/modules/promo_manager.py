"""
Promo Manager Module - Handles promotional content
"""

import random
from pathlib import Path
from moviepy.editor import (
    ImageClip, CompositeVideoClip, TextClip, ColorClip
)
from moviepy.video.fx.all import fadein, fadeout

class PromoManager:
    """Manages promotional content for videos"""
    
    def __init__(self, promotional_folder):
        self.promotional_folder = Path(promotional_folder)
        self.promotional_images = []
        self.load_promotional_images()
    
    def load_promotional_images(self):
        """Load promotional images from the promotional folder"""
        if self.promotional_folder.exists():
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            for ext in image_extensions:
                self.promotional_images.extend(list(self.promotional_folder.glob(f"*{ext}")))
                self.promotional_images.extend(list(self.promotional_folder.glob(f"*{ext.upper()}")))
            
            if self.promotional_images:
                print(f"📸 Loaded {len(self.promotional_images)} promotional images")
                for img in self.promotional_images[:5]:
                    print(f"   - {img.name}")
                if len(self.promotional_images) > 5:
                    print(f"   ... and {len(self.promotional_images) - 5} more")
            else:
                print("⚠️ No promotional images found in the promotional folder")
        else:
            print(f"⚠️ Promotional folder not found: {self.promotional_folder}")
    
    def get_promotional_clip(self, duration=5, info=None):
        """Get a promotional clip from the promotional folder"""
        if not self.promotional_images:
            return self.create_promotional_end_card(duration, info)
        
        promo_image_path = random.choice(self.promotional_images)
        print(f"📸 Using promotional image: {promo_image_path.name}")
        
        try:
            promo_clip = ImageClip(str(promo_image_path))
            target_width = 1080
            target_height = 1920
            
            original_width, original_height = promo_clip.size
            original_aspect = original_width / original_height
            target_aspect = target_width / target_height
            
            if original_aspect > target_aspect:
                promo_clip = promo_clip.resize(width=target_width)
                y_pos = (target_height - promo_clip.h) // 2
                promo_clip = promo_clip.set_position(('center', y_pos))
                
                bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
                bg = bg.set_duration(duration)
                promo_clip = CompositeVideoClip([bg, promo_clip])
            else:
                promo_clip = promo_clip.resize(height=target_height)
                x_pos = (target_width - promo_clip.w) // 2
                promo_clip = promo_clip.set_position((x_pos, 'center'))
                
                bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
                bg = bg.set_duration(duration)
                promo_clip = CompositeVideoClip([bg, promo_clip])
            
            promo_clip = promo_clip.set_duration(duration)
            promo_clip = fadein(promo_clip, 0.5)
            promo_clip = fadeout(promo_clip, 0.5)
            
            return promo_clip
            
        except Exception as e:
            print(f"⚠️ Error loading promotional image: {e}")
            return self.create_promotional_end_card(duration, info)
    
    def create_promotional_end_card(self, duration=5, info=None):
        """Create a promotional end card for online chess classes"""
        bg = ColorClip(size=(1080, 1920), color=(20, 20, 30), duration=duration)
        
        overlays = []
        
        main_title = "♟️ ONLINE CHESS CLASSES"
        title = TextClip(
            main_title,
            fontsize=70,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=3,
            size=(900, None),
            method='label'
        ).set_position(('center', 200))
        overlays.append(title)
        
        subtitle = TextClip(
            "Learn from Expert Coaches",
            fontsize=45,
            color='gold',
            font='Arial',
            size=(800, None),
            method='label'
        ).set_position(('center', 350))
        overlays.append(subtitle)
        
        details_text = []
        if info:
            if info.get('tournament_name') and info.get('tournament_name') != "Chess Tournament":
                details_text.append(f"🏆 {info.get('tournament_name')}")
            if info.get('venue') and info.get('venue') != "Online Classes Available":
                details_text.append(f"📍 {info.get('venue')}")
            dates = info.get('dates', [])
            if dates:
                details_text.append(f"📅 {', '.join(dates)}")
        
        if details_text:
            details = TextClip(
                '\n'.join(details_text[:3]),
                fontsize=32,
                color='white',
                font='Arial',
                method='label',
                size=(800, None)
            ).set_position(('center', 500))
            overlays.append(details)
        
        features = TextClip(
            "• All Levels Welcome\n• Individual Attention\n• Flexible Timings\n• Tournament Preparation",
            fontsize=35,
            color='#CCCCCC',
            font='Arial',
            method='label',
            size=(800, None)
        ).set_position(('center', 800))
        overlays.append(features)
        
        contact_text = "📧 akhil.chess3@gmail.com"
        if info and info.get('email'):
            email = info['email'][0] if info['email'] else 'akhil.chess3@gmail.com'
            contact_text = f"📧 {email}"
        
        contact = TextClip(
            contact_text,
            fontsize=40,
            color='lightblue',
            font='Arial',
            method='label',
            size=(800, None)
        ).set_position(('center', 1300))
        overlays.append(contact)
        
        cta = TextClip(
            "📧 Contact us to Register!",
            fontsize=45,
            color='#FFD700',
            font='Arial-Bold',
            method='label'
        ).set_position(('center', 1700))
        overlays.append(cta)
        
        end_card = CompositeVideoClip([bg] + overlays)
        end_card = end_card.set_duration(duration)
        end_card = fadein(end_card, 0.5)
        end_card = fadeout(end_card, 0.5)
        
        return end_card