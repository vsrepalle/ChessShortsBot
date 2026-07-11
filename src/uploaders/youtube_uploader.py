"""
YouTube Uploader Module - Handles uploading videos to YouTube
"""

import os
import pickle
import logging
import sys
import json
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

class YouTubeUploader:
    """Handles uploading videos to YouTube with detailed debugging"""
    
    def __init__(self, client_secrets_file=None):
        self.debugger = UploadDebugger("upload_debug.log")
        self.debugger.log_step("YouTubeUploader Initialization", {
            "client_secrets_file": client_secrets_file,
            "google_available": GOOGLE_AVAILABLE
        })
        
        self.client_secrets_file = client_secrets_file or CLIENT_SECRETS_FILE
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.youtube = None
        self.is_authenticated = False
        
        # Log client secrets file info
        self.debugger.log_file_info(self.client_secrets_file, "Client Secrets File")
        
        if not GOOGLE_AVAILABLE:
            self.debugger.log_error("Google API libraries not available", {
                "error": "ImportError",
                "suggestion": "pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            })
            return
        
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with YouTube API with detailed debugging"""
        self.debugger.log_step("YouTube Authentication")
        
        if not GOOGLE_AVAILABLE:
            self.debugger.log_error("Cannot authenticate - Google libraries not available")
            return False
        
        credentials = None
        token_file = 'token.pickle'
        
        self.debugger.log_file_info(token_file, "Token File")
        
        # Load existing credentials
        try:
            if os.path.exists(token_file):
                self.debugger.log("Loading existing credentials from token.pickle")
                with open(token_file, 'rb') as token:
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
                    self.debugger.log_file_info(self.client_secrets_file, "Client Secrets File")
                    
                    if not os.path.exists(self.client_secrets_file):
                        error_msg = f"Client secrets file not found: {self.client_secrets_file}"
                        self.debugger.log_error(error_msg, {
                            "suggestion": "Download client_secret.json from Google Cloud Console",
                            "path": self.client_secrets_file
                        })
                        print(f"\n❌ {error_msg}")
                        print("   Please download client_secret.json from Google Cloud Console")
                        print("   Save it as: client_secret.json in the project root")
                        return False
                    
                    self.debugger.log("Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_file, SCOPES)
                    self.debugger.log("OAuth flow created successfully")
                    
                    self.debugger.log("Starting local server for authentication...")
                    credentials = flow.run_local_server(port=0)
                    self.debugger.log("✅ Authentication completed successfully")
                
                # Save credentials
                self.debugger.log("Saving credentials to token.pickle")
                with open(token_file, 'wb') as token:
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
    
    def upload_video(self, video_path, metadata):
        """
        Upload a video to YouTube with detailed debugging
        """
        self.debugger.log_step("Upload Video to YouTube")
        
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
            # Prepare metadata
            self.debugger.log_step("Preparing YouTube Metadata")
            
            title = metadata.get('Title', 'Chess Short')
            description = metadata.get('YouTube Description', '') or metadata.get('Description', '')
            hashtags = metadata.get('YouTube Hashtags', '')
            
            self.debugger.log(f"Title: {title}")
            self.debugger.log(f"Description length: {len(description)} characters")
            self.debugger.log(f"Hashtags: {hashtags}")
            
            if not description:
                self.debugger.log("No description provided, generating default")
                description = f"🏆 {title}\n\n♟️ Check out this chess content!"
                if hashtags:
                    description += f"\n\n{hashtags}"
                self.debugger.log(f"Generated description: {description[:100]}...")
            
            # Prepare video body
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': hashtags.replace('#', '').split() if hashtags else [],
                    'categoryId': '22'  # 22 = People & Blogs
                },
                'status': {
                    'privacyStatus': 'public',
                    'madeForKids': False
                }
            }
            
            self.debugger.log(f"Video body prepared: {json.dumps(body, indent=2, default=str)[:500]}...")
            
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
            self.debugger.log_step("Executing Upload")
            print(f"\n📤 Uploading video to YouTube...")
            print(f"   Title: {title}")
            print(f"   File: {video_path_str}")
            
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
                    self.debugger.log_success(f"Video uploaded successfully! Video ID: {video_id}")
                    print(f"✅ Video uploaded successfully!")
                    print(f"   Video ID: {video_id}")
                    print(f"   URL: https://www.youtube.com/watch?v={video_id}")
                    
                    # Save summary
                    self.debugger.save_summary()
                    
                    return {
                        'video_id': video_id,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'title': title
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
    
    def set_privacy(self, video_id, privacy_status='public'):
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
