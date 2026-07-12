"""
YouTube Uploader Module - Handles uploading videos to YouTube with channel support
"""

import os
import pickle
import logging
import sys
import json
import re
import time
from pathlib import Path
from datetime import datetime

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    from googleapiclient.errors import ResumableUploadError
    GOOGLE_AVAILABLE = True
except ImportError as e:
    GOOGLE_AVAILABLE = False
    print(f"⚠️ Google API libraries not installed: {e}")
    print("   Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")

from .upload_debugger import UploadDebugger

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS_FILE = "client_secret.json"

# Default hashtags for all videos - ALWAYS INCLUDED
DEFAULT_HASHTAGS = ["#Chess", "#ChessPuzzles", "#ChessTournaments", "#ChessNews"]

class YouTubeUploader:
    """Handles uploading videos to YouTube with channel support"""
    
    def __init__(self, client_secrets_file=None, channel_id=None):
        """
        Initialize the YouTube uploader
        
        Args:
            client_secrets_file: Path to client_secrets.json file
            channel_id: Specific YouTube channel ID to upload to (optional)
        """
        self.debugger = UploadDebugger("upload_debug.log")
        self.debugger.log_step("YouTubeUploader Initialization", {
            "client_secrets_file": client_secrets_file,
            "channel_id": channel_id,
            "google_available": GOOGLE_AVAILABLE
        })
        
        self.client_secrets_file = client_secrets_file or CLIENT_SECRETS_FILE
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.youtube = None
        self.is_authenticated = False
        self.channel_id = channel_id  # Specific channel to upload to
        self.token_file = None  # Will be set per channel
        
        # Log client secrets file info
        self.debugger.log_file_info(self.client_secrets_file, "Client Secrets File")
        
        if not GOOGLE_AVAILABLE:
            self.debugger.log_error("Google API libraries not available", {
                "error": "ImportError",
                "suggestion": "pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            })
            return
        
        self.authenticate()
    
    def authenticate(self, client_secrets_file=None, token_file=None):
        """
        Authenticate with YouTube API with detailed debugging
        
        Args:
            client_secrets_file: Path to client_secrets.json (optional)
            token_file: Path to token.pickle (optional)
        """
        self.debugger.log_step("YouTube Authentication")
        
        if not GOOGLE_AVAILABLE:
            self.debugger.log_error("Cannot authenticate - Google libraries not available")
            return False
        
        # Use provided credentials or defaults
        client_secret_path = client_secrets_file or self.client_secrets_file
        token_path = token_file or self.token_file or "token.pickle"
        
        client_secret = Path(client_secret_path)
        token_file_path = Path(token_path)
        
        print("\n==============================")
        print("YOUTUBE AUTH")
        print("==============================")
        print("Client Secret :", client_secret)
        print("Token File    :", token_file_path)
        print("==============================")
        
        self.debugger.log_file_info(str(token_file_path), "Token File")
        
        credentials = None
        
        # Load existing credentials
        try:
            if token_file_path.exists():
                self.debugger.log("Loading existing credentials from token.pickle")
                with open(token_file_path, 'rb') as token:
                    credentials = pickle.load(token)
                self.debugger.log("✅ Credentials loaded successfully")
            else:
                self.debugger.log("No existing token file found")
        except Exception as e:
            self.debugger.log_error(f"Error loading token file: {e}")
        
        # Check if credentials are valid
        if credentials:
            self.debugger.log(f"Credentials valid: {credentials.valid}")
            self.debugger.log(f"Credentials expired: {credentials.expired}")
            if hasattr(credentials, 'refresh_token'):
                self.debugger.log(f"Has refresh token: {bool(credentials.refresh_token)}")
        
        # If no valid credentials, get new ones
        if not credentials or not credentials.valid:
            self.debugger.log("Getting new credentials...")
            
            try:
                if credentials and credentials.expired and credentials.refresh_token:
                    self.debugger.log("Refreshing expired credentials...")
                    credentials.refresh(Request())
                    self.debugger.log("✅ Credentials refreshed successfully")
                else:
                    self.debugger.log("Checking for client secrets file...")
                    self.debugger.log_file_info(str(client_secret), "Client Secrets File")
                    
                    if not client_secret.exists():
                        error_msg = f"Client secrets file not found: {client_secret}"
                        self.debugger.log_error(error_msg, {
                            "suggestion": "Download client_secret.json from Google Cloud Console",
                            "path": str(client_secret)
                        })
                        print(f"\n❌ {error_msg}")
                        print("   Please download client_secret.json from Google Cloud Console")
                        print("   Save it as: client_secret.json in the project root or channel credentials folder")
                        return False
                    
                    self.debugger.log("Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
                    self.debugger.log("OAuth flow created successfully")
                    
                    self.debugger.log("Starting local server for authentication...")
                    credentials = flow.run_local_server(port=0)
                    
                    print("\n✅ OAuth completed")
                    print(f"Saving token to: {token_file_path}")
                    self.debugger.log("✅ Authentication completed successfully")
                
                # Save credentials
                self.debugger.log("Saving credentials to token.pickle")
                token_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(token_file_path, "wb") as token:
                    pickle.dump(credentials, token)
                self.debugger.log("✅ Credentials saved")
                
            except Exception as e:
                self.debugger.log_error(f"Authentication failed: {e}", {
                    "error_type": type(e).__name__
                })
                return False
        else:
            self.debugger.log("Using existing valid credentials")
        
        # Build YouTube service
        try:
            self.debugger.log("Building YouTube service...")
            self.youtube = build(
                self.api_service_name, self.api_version, credentials=credentials)
            self.debugger.log("✅ YouTube service built successfully")
            self.is_authenticated = True
            print("✅ YouTube API authenticated successfully!")
            return True
        except Exception as e:
            self.debugger.log_error(f"Failed to build YouTube service: {e}")
            print(f"❌ Failed to authenticate with YouTube: {e}")
            return False
    
    def get_channel_id(self, channel_name):
        """
        Get YouTube channel ID from channel name
        This searches for the channel by name
        """
        if not self.youtube:
            return None
        
        try:
            # Search for the channel by name
            self.debugger.log(f"Searching for channel: {channel_name}")
            request = self.youtube.search().list(
                part='snippet',
                q=channel_name,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            
            if response.get('items'):
                channel_id = response['items'][0]['snippet']['channelId']
                channel_title = response['items'][0]['snippet']['title']
                self.debugger.log(f"✅ Found channel: {channel_title} -> {channel_id}")
                print(f"✅ Found channel: {channel_title}")
                return channel_id
            else:
                self.debugger.log(f"⚠️ Channel not found: {channel_name}")
                print(f"⚠️ Channel '{channel_name}' not found")
                return None
                
        except Exception as e:
            self.debugger.log_error(f"Error searching for channel: {e}")
            print(f"❌ Error searching for channel: {e}")
            return None
    
    def get_default_hashtags(self):
        """Get default hashtags for all videos"""
        return " ".join(DEFAULT_HASHTAGS)
    
    def upload_video(self, video_path, metadata, channel_name=None):
        """
        Upload a video to YouTube as PRIVATE - ALWAYS PRIVATE
        
        Args:
            video_path: Path to the video file
            metadata: Dictionary with video metadata
            channel_name: Name of the channel folder (e.g., "BrainRush Puzzles")
        """
        self.debugger.log_step(f"Upload Video to YouTube (PRIVATE - FORCED)")
        self.debugger.log(f"Channel: {channel_name or 'Default'}")

        # Handle channel-specific credentials
        if channel_name:
            credentials_dir = Path("inputs/pending/channels") / channel_name / "credentials"
            client_secret = credentials_dir / "client_secret.json"
            token_file = credentials_dir / "token.pickle"

            if client_secret.exists():
                self.client_secrets_file = str(client_secret)
                self.token_file = str(token_file)
                print(f"📂 Using channel credentials: {credentials_dir}")
                # Re-authenticate with channel credentials
                self.authenticate(
                    client_secrets_file=str(client_secret),
                    token_file=str(token_file)
                )
        
        # Log input parameters
        self.debugger.log_file_info(video_path, "Video File")
        self.debugger.log_metadata(metadata, "Metadata")
        
        # Check authentication
        if not self.youtube:
            self.debugger.log_error("Not authenticated - youtube service not available")
            print("❌ Not authenticated. Please check your credentials.")
            return None
        
        if not self.is_authenticated:
            self.debugger.log_error("Not authenticated - authentication failed previously")
            print("❌ Not authenticated. Please check your credentials.")
            return None
        
        # Check video file
        if not video_path:
            self.debugger.log_error("Video path is None or empty")
            return None
        
        video_path_str = str(video_path)
        if not os.path.exists(video_path_str):
            self.debugger.log_error(f"Video file not found: {video_path_str}")
            return None
        
        # Check file size
        file_size = os.path.getsize(video_path_str)
        self.debugger.log(f"File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
        if file_size == 0:
            self.debugger.log_error("Video file is empty (0 bytes)")
            return None
        
        try:
            # Get channel ID if channel name is provided
            upload_channel_id = None
            if channel_name:
                print(f"\n📺 Using channel: {channel_name}")
                # Don't search for channel, just use the credentials we already loaded
                upload_channel_id = self.channel_id
            
            # Prepare metadata
            self.debugger.log_step("Preparing YouTube Metadata")
            
            title = metadata.get('Title', 'Chess Short')
            description = metadata.get('YouTube Description', '') or metadata.get('Description', '')
            
            # ALWAYS include default hashtags
            hashtags = self.get_default_hashtags()
            
            # Add channel name as hashtag
            if channel_name:
                # Clean channel name for hashtag
                clean_channel = re.sub(r'[^a-zA-Z0-9]', '', channel_name.replace(' ', ''))
                if clean_channel and len(clean_channel) > 3:
                    hashtags += f" #{clean_channel}"
            
            # Add any additional hashtags from metadata
            if metadata.get('YouTube Hashtags'):
                additional = metadata.get('YouTube Hashtags').replace('#', '').split()
                for tag in additional[:3]:  # Limit additional tags
                    if tag not in hashtags:
                        hashtags += f" #{tag}"
            
            self.debugger.log(f"Title: {title}")
            self.debugger.log(f"Description length: {len(description)} characters")
            self.debugger.log(f"Hashtags: {hashtags}")
            self.debugger.log(f"Channel ID: {upload_channel_id or 'Default'}")
            
            if not description:
                self.debugger.log("No description provided, generating default")
                description = f"♟️ Chess Short\n\n{hashtags}"
                self.debugger.log(f"Generated description: {description[:100]}...")
            elif hashtags not in description:
                description = f"{description}\n\n{hashtags}"
            
            # Prepare video body - FORCE PRIVATE
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': hashtags.replace('#', '').split() if hashtags else [],
                    'categoryId': '22'  # 22 = People & Blogs
                },
                'status': {
                    'privacyStatus': 'private',  # FORCED PRIVATE
                    'madeForKids': False,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Add channel ID if found
            if upload_channel_id:
                body['snippet']['channelId'] = upload_channel_id
            
            self.debugger.log(f"✅ Video privacy: PRIVATE (FORCED)")
            self.debugger.log(f"✅ Channel: {channel_name or 'Default'}")
            
            # Prepare media upload
            self.debugger.log_step("Preparing Media Upload")
            self.debugger.log(f"Video file: {video_path_str}")
            
            try:
                media = MediaFileUpload(
                    video_path_str,
                    chunksize=-1,
                    resumable=True
                )
                self.debugger.log("✅ MediaFileUpload created successfully")
            except Exception as e:
                self.debugger.log_error(f"Failed to create MediaFileUpload: {e}")
                return None
            
            # Create upload request
            self.debugger.log_step("Creating YouTube Upload Request")
            
            try:
                request = self.youtube.videos().insert(
                    part=','.join(body.keys()),
                    body=body,
                    media_body=media
                )
                self.debugger.log("✅ Upload request created successfully")
            except Exception as e:
                self.debugger.log_error(f"Failed to create upload request: {e}")
                return None
            
            # Execute upload
            self.debugger.log_step("Executing Upload (PRIVATE)")
            print(f"\n📤 Uploading video to YouTube...")
            print(f"   Title: {title}")
            print(f"   Channel: {channel_name or 'Default'}")
            print(f"   🔒 Privacy: PRIVATE (forced)")
            print(f"   📋 Hashtags: {hashtags}")
            
            response = None
            upload_complete = False
            attempt = 0
            max_attempts = 3
            
            while not upload_complete and attempt < max_attempts:
                attempt += 1
                self.debugger.log(f"Upload attempt {attempt}/{max_attempts}")
                
                try:
                    status, response = request.next_chunk()
                    
                    if status:
                        progress = int(status.progress() * 100)
                        self.debugger.log(f"Upload progress: {progress}%")
                        print(f"   Upload progress: {progress}%")
                    
                    if response:
                        self.debugger.log("✅ Upload complete - received response")
                        upload_complete = True
                        
                except HttpError as e:
                    self.debugger.log_error(f"YouTube API error (attempt {attempt}): {e}")
                    print(f"   ⚠️ API error: {e}")
                    if attempt >= max_attempts:
                        raise
                    print(f"   Retrying in 5 seconds...")
                    time.sleep(5)
                    
                except ResumableUploadError as e:
                    self.debugger.log_error(f"Resumable upload error (attempt {attempt}): {e}")
                    print(f"   ⚠️ Upload error: {e}")
                    if attempt >= max_attempts:
                        raise
                    print(f"   Retrying in 5 seconds...")
                    time.sleep(5)
                    
                except Exception as e:
                    self.debugger.log_error(f"Unexpected error (attempt {attempt}): {e}")
                    if attempt >= max_attempts:
                        raise
                    print(f"   ⚠️ Error: {e}")
                    print(f"   Retrying in 5 seconds...")
                    time.sleep(5)
            
            # Process response
            if response:
                video_id = response.get('id')
                self.debugger.log_step("Upload Complete - Processing Response")
                self.debugger.log(f"Video ID: {video_id}")
                
                if video_id:
                    self.debugger.log_success(f"Video uploaded as PRIVATE! Video ID: {video_id}")
                    print(f"\n✅ Video uploaded successfully!")
                    print(f"   📺 Channel: {channel_name or 'Default'}")
                    print(f"   🔒 Privacy: PRIVATE")
                    print(f"   🆔 Video ID: {video_id}")
                    print(f"   🔗 URL: https://www.youtube.com/watch?v={video_id}")
                    print(f"   📋 Hashtags: {hashtags}")
                    
                    # Save summary
                    self.debugger.save_summary()
                    
                    return {
                        'video_id': video_id,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'title': title,
                        'channel': channel_name or 'Default',
                        'privacy': 'private',
                        'hashtags': hashtags
                    }
                else:
                    self.debugger.log_error("No video ID in response", {"response": response})
                    print("❌ Upload failed - no video ID in response")
                    return None
            else:
                self.debugger.log_error("Upload failed - no response from YouTube")
                print("❌ Upload failed - no response from YouTube")
                return None
                
        except HttpError as e:
            self.debugger.log_error(f"YouTube API error: {e}")
            print(f"❌ YouTube API error: {e}")
            return None
        except ResumableUploadError as e:
            self.debugger.log_error(f"Resumable upload error: {e}")
            print(f"❌ Upload error: {e}")
            return None
        except Exception as e:
            self.debugger.log_error(f"Error uploading video: {e}")
            print(f"❌ Error uploading video: {e}")
            self.debugger.save_summary()
            return None
    
    def set_privacy(self, video_id, privacy_status='private'):
        """Change privacy status of a video"""
        if not self.youtube:
            return False
        
        try:
            self.youtube.videos().update(
                part='status',
                body={
                    'id': video_id,
                    'status': {
                        'privacyStatus': privacy_status
                    }
                }
            ).execute()
            print(f"✅ Video privacy updated to: {privacy_status}")
            return True
        except Exception as e:
            logging.error(f"Error updating privacy: {e}")
            return False