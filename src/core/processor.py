"""
Core Processor - Orchestrates the processing pipeline
"""

import os
import logging
import shutil
from pathlib import Path
from datetime import datetime
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
        
        # Define channels folder
        self.channels_dir = Path("inputs/pending/channels")
        self.channels_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize YouTube uploader
        self.youtube_uploader = None
        self.youtube_available = False
        
        try:
            from src.uploaders.youtube_uploader import YouTubeUploader
            client_secrets = self.config.get('youtube', {}).get('client_secrets', 'client_secret.json')
            self.youtube_uploader = YouTubeUploader(client_secrets)
            self.youtube_available = True
            print("âœ… YouTube uploader initialized successfully")
        except ImportError as e:
            print(f"âš ï¸ YouTube uploader not available: {e}")
            print("   Install required packages: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        except Exception as e:
            print(f"âš ï¸ Failed to initialize YouTube uploader: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80)
        print("ðŸš€ PIPELINE INITIALIZED")
        print("="*80)
        print(f"ðŸ“ Output directory: {self.output_dir}")
        print(f"ðŸ“ Uploaded directory: {self.uploaded_dir}")
        print(f"ðŸ“ Channels directory: {self.channels_dir}")
        print(f"ðŸ“º YouTube upload: {'âœ… Enabled' if self.youtube_available else 'âŒ Disabled'}")
        print("="*80 + "\n")
    
    def detect_channel(self, file_path):
        """
        Detect which channel folder the file is in
        
        Returns:
            str: Channel name or None if not in a channel folder
        """
        file_path = Path(file_path)
        parent = file_path.parent
        
        print(f"ðŸ” Detecting channel for: {file_path}")
        print(f"   Parent: {parent}")
        print(f"   Grandparent: {parent.parent}")
        print(f"   Channels dir: {self.channels_dir}")
        
        # Check if the file is in a channel folder
        # The structure is: inputs/pending/channels/ChannelName/file.jpg
        if str(parent.parent.parent).lower() == str(self.channels_dir).lower():
            channel_name = parent.parent.name
            print(f"âœ… Channel detected: {channel_name}")
            return channel_name
        
        # Check if it's directly in channels folder
        if str(parent).lower() == str(self.channels_dir).lower():
            print("âš ï¸ File is directly in channels folder, not in a subfolder")
            return None
        
        # Check if it's in the regular pending folder
        if str(parent).lower() == str(Path("inputs/pending")).lower():
            print("ðŸ“ File is in pending folder (no channel)")
            return None
        
        print("ðŸ“ No channel detected")
        return None
    
    def process_file(self, file_path):
        """Process a file based on its type"""
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()
        
        logging.info(f"Processing file: {file_path}")
        print(f"\nðŸ“ Processing file: {file_path}")
        
        # Detect channel
        channel_name = self.detect_channel(file_path)
        print(f"ðŸ“º Channel: {channel_name or 'Default'}")
        
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
                "error": f"Unsupported file type: {file_ext}",
                "channel": channel_name
            }
    
    def process_brochure(self, file_path):
        """Process a brochure image file"""
        return self.brochure_processor.process(file_path)
    
    def process_pgn(self, file_path):
        """Process a PGN file"""
        return self.pgn_processor.process(file_path)
    
    def upload_video(self, video_path, metadata, channel_name=None):
        """
        Upload the video to YouTube with channel support
        
        Args:
            video_path: Path to the video file
            metadata: Dictionary with video metadata
            channel_name: Name of the channel to upload to
        """
        print(f"\nðŸ“¤ UPLOAD FUNCTION CALLED")
        print(f"   Video path: {video_path}")
        print(f"   Channel: {channel_name or 'Default'}")
        print(f"   YouTube available: {self.youtube_available}")
        
        if not video_path or not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            print(f"âŒ Video file not found: {video_path}")
            return False
        
        try:
            # Check if YouTube uploader is available
            if self.youtube_available and self.youtube_uploader:
                print(f"\nðŸ“¤ Uploading to YouTube...")
                if channel_name:
                    print(f"   ðŸ“º Channel: {channel_name}")
                
                # Prepare metadata for YouTube
                youtube_metadata = {
                    'Title': metadata.get('youtube_title', metadata.get('Title', 'Chess Short')),
                    'YouTube Description': metadata.get('youtube_description', ''),
                    'YouTube Hashtags': metadata.get('youtube_hashtags', '')
                }
                
                print(f"   ðŸ“‹ Title: {youtube_metadata['Title']}")
                print(f"   ðŸ“‹ Hashtags: {youtube_metadata['YouTube Hashtags']}")
                
                # Upload to YouTube with channel support
                print(f"ðŸš€ Calling youtube_uploader.upload_video()...")
                result = self.youtube_uploader.upload_video(
                    video_path, 
                    youtube_metadata,
                    channel_name=channel_name
                )
                
                if result:
                    print(f"âœ… Video uploaded to YouTube successfully!")
                    print(f"   ðŸ“º Channel: {result.get('channel', 'Default')}")
                    print(f"   ðŸ†” Video ID: {result.get('video_id')}")
                    print(f"   ðŸ”— URL: {result.get('url')}")
                    
                    # Also save a local copy
                    video_name = Path(video_path).name
                    uploaded_path = self.uploaded_dir / video_name
                    shutil.copy2(video_path, uploaded_path)
                    print(f"ðŸ“ Local copy saved: {uploaded_path}")
                    
                    # Save upload info
                    upload_info = {
                        'video_id': result.get('video_id'),
                        'url': result.get('url'),
                        'title': result.get('title'),
                        'channel': result.get('channel'),
                        'uploaded_at': datetime.now().isoformat()
                    }
                    
                    info_file = self.uploaded_dir / f"{Path(video_path).stem}_upload_info.json"
                    import json
                    with open(info_file, 'w') as f:
                        json.dump(upload_info, f, indent=2)
                    print(f"ðŸ“‹ Upload info saved: {info_file}")
                    
                    return True
                else:
                    print("âŒ YouTube upload returned None (failed)")
                    return False
            else:
                # Fallback to local copy only
                print(f"\nðŸ“¤ YouTube upload not available - saving local copy...")
                print(f"   YouTube available: {self.youtube_available}")
                print(f"   YouTube uploader: {self.youtube_uploader}")
                
                video_name = Path(video_path).name
                uploaded_path = self.uploaded_dir / video_name
                shutil.copy2(video_path, uploaded_path)
                print(f"ðŸ“ Local copy saved: {uploaded_path}")
                if channel_name:
                    print(f"   ðŸ“º Channel: {channel_name}")
                print(f"   Title: {metadata.get('Title', 'N/A')}")
                print("âš ï¸ This is a SIMULATED upload. To enable real YouTube upload:")
                print("   1. Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
                print("   2. Get client_secret.json from Google Cloud Console")
                return True
            
        except Exception as e:
            logging.error(f"Error uploading video: {e}")
            print(f"âŒ Error uploading video: {e}")
            import traceback
            traceback.print_exc()
            return False

