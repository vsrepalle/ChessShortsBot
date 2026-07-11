"""
Core Processor - Orchestrates the processing pipeline
"""

import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
from src.processors.brochure_processor import BrochureProcessor
from src.processors.pgn_processor import PGNProcessor

class Pipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config=None, config_path=None):
        """
        Initialize the pipeline
        
        Args:
            config: Configuration dictionary (optional)
            config_path: Path to config file (optional)
        """
        self.config = config or {}
        if config_path and os.path.exists(config_path):
            import yaml
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        
        self.brochure_processor = BrochureProcessor(self.config)
        self.pgn_processor = PGNProcessor(self.config)
        self.output_dir = Path("output/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.uploaded_dir = Path("output/uploaded")
        self.uploaded_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize YouTube uploader
        try:
            from src.uploaders.youtube_uploader import YouTubeUploader
            client_secrets = self.config.get('youtube', {}).get('client_secrets', 'client_secret.json')
            self.youtube_uploader = YouTubeUploader(client_secrets)
            self.youtube_available = True
            print("? YouTube uploader initialized")
        except ImportError as e:
            print(f"?? YouTube uploader not available: {e}")
            print("   Install required packages: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            self.youtube_uploader = None
            self.youtube_available = False
        except Exception as e:
            print(f"?? Failed to initialize YouTube uploader: {e}")
            self.youtube_uploader = None
            self.youtube_available = False
        
        print("\n" + "="*80)
        print("?? PIPELINE INITIALIZED")
        print("="*80)
        print(f"?? Output directory: {self.output_dir}")
        print(f"?? Uploaded directory: {self.uploaded_dir}")
        print(f"?? YouTube upload: {'Enabled' if self.youtube_available else 'Disabled'}")
        print("="*80 + "\n")
    
    def process_file(self, file_path):
        """Process a file based on its type"""
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()
        
        logging.info(f"Processing file: {file_path}")
        
        if file_ext == '.pgn':
            return self.pgn_processor.process(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
            return self.brochure_processor.process(file_path)
        else:
            logging.warning(f"Unsupported file type: {file_ext}")
            return {
                "video": None,
                "thumbnail": None,
                "metadata": {},
                "skipped": True,
                "error": f"Unsupported file type: {file_ext}"
            }
    
    def process_brochure(self, file_path):
        """Process a brochure image file"""
        return self.brochure_processor.process(file_path)
    
    def process_pgn(self, file_path):
        """Process a PGN file"""
        return self.pgn_processor.process(file_path)
    
    def upload_video(self, video_path, metadata):
        """
        Upload the video to YouTube
        """
        if not video_path or not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            return False
        
        try:
            # Check if YouTube uploader is available
            if self.youtube_available and self.youtube_uploader:
                print(f"\n?? Uploading to YouTube...")
                
                # Prepare metadata for YouTube
                youtube_metadata = {
                    'Title': metadata.get('youtube_title', metadata.get('Title', 'Chess Short')),
                    'YouTube Description': metadata.get('youtube_description', ''),
                    'YouTube Hashtags': metadata.get('youtube_hashtags', '')
                }
                
                # Upload to YouTube
                result = self.youtube_uploader.upload_video(video_path, youtube_metadata)
                
                if result:
                    print(f"? Video uploaded to YouTube successfully!")
                    print(f"   URL: {result.get('url')}")
                    
                    # Also save a local copy
                    video_name = Path(video_path).name
                    uploaded_path = self.uploaded_dir / video_name
                    shutil.copy2(video_path, uploaded_path)
                    print(f"?? Local copy saved: {uploaded_path}")
                    
                    # Save upload info
                    upload_info = {
                        'video_id': result.get('video_id'),
                        'url': result.get('url'),
                        'title': result.get('title'),
                        'uploaded_at': datetime.now().isoformat()
                    }
                    
                    info_file = self.uploaded_dir / f"{Path(video_path).stem}_upload_info.json"
                    import json
                    with open(info_file, 'w') as f:
                        json.dump(upload_info, f, indent=2)
                    print(f"?? Upload info saved: {info_file}")
                    
                    return True
                else:
                    print("? YouTube upload failed!")
                    return False
            else:
                # Fallback to local copy only
                print(f"\n?? YouTube upload not available - saving local copy...")
                video_name = Path(video_path).name
                uploaded_path = self.uploaded_dir / video_name
                shutil.copy2(video_path, uploaded_path)
                print(f"?? Local copy saved: {uploaded_path}")
                print(f"   Title: {metadata.get('Title', 'N/A')}")
                print(f"   Tournament: {metadata.get('Tournament', 'N/A')}")
                print(f"   Venue: {metadata.get('Venue', 'N/A')}")
                print(f"   Dates: {metadata.get('Dates', 'N/A')}")
                print("?? This is a SIMULATED upload. To enable real YouTube upload:")
                print("   1. Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
                print("   2. Get client_secret.json from Google Cloud Console")
                return True
            
        except Exception as e:
            logging.error(f"Error uploading video: {e}")
            print(f"? Error uploading video: {e}")
            import traceback
            traceback.print_exc()
            return False
