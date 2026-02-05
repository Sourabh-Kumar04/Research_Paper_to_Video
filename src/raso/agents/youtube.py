"""
YouTube Integration Agent for the RASO platform.

Handles YouTube API authentication, video upload, and metadata application.
"""

import os
import asyncio
from typing import Dict, Any, Optional

from agents.base import BaseAgent
from backend.models import AgentType
from backend.models.state import RASOMasterState
from backend.models.video import VideoAsset, VideoMetadata
from agents.retry import retry


class YouTubeAgent(BaseAgent):
    """Agent responsible for YouTube integration."""
    
    name = "YouTubeAgent"
    description = "Handles YouTube video upload and metadata application"
    
    def __init__(self, agent_type: AgentType):
        """Initialize YouTube agent."""
        super().__init__(agent_type)
    
    @retry(max_attempts=3, base_delay=5.0)
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """Execute YouTube upload if configured."""
        self.validate_input(state)
        
        try:
            video = state.video
            metadata = state.metadata
            
            self.log_progress("Starting YouTube upload process", state)
            
            # Check if YouTube integration is configured
            if not self._is_youtube_configured():
                self.log_progress("YouTube integration not configured, skipping upload", state)
                # Complete the pipeline without upload
                state.progress.current_step = "completed"
                state.progress.overall_progress = 1.0
                state.current_agent = None
                return state
            
            # Attempt real YouTube upload
            youtube_url = await self._upload_to_youtube(video, metadata)
            
            if youtube_url:
                self.log_progress(f"Video uploaded successfully to YouTube: {youtube_url}", state)
            else:
                self.log_progress("YouTube upload failed, but pipeline completed", state)
            
            # Complete the pipeline
            state.progress.current_step = "completed"
            state.progress.overall_progress = 1.0
            state.current_agent = None
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: RASOMasterState) -> None:
        """Validate input state."""
        if not state.video:
            raise ValueError("Video not found in state")
        
        if not state.metadata:
            raise ValueError("Metadata not found in state")
    
    def _is_youtube_configured(self) -> bool:
        """Check if YouTube API is properly configured."""
        try:
            return (
                hasattr(self.config, 'youtube') and
                self.config.youtube.client_id and
                self.config.youtube.client_secret and
                self.config.youtube.refresh_token
            )
        except:
            return False
    
    async def _upload_to_youtube(self, video: VideoAsset, metadata: VideoMetadata) -> Optional[str]:
        """Upload video to YouTube using the API."""
        try:
            # Check if video file exists
            if not Path(video.file_path).exists():
                self.logger.error(f"Video file not found: {video.file_path}")
                return None
            
            # Try to use YouTube API
            youtube_service = await self._get_youtube_service()
            if not youtube_service:
                self.logger.warning("YouTube service not available")
                return None
            
            # Prepare video metadata
            video_metadata = {
                'snippet': {
                    'title': metadata.title,
                    'description': metadata.description,
                    'tags': metadata.tags,
                    'categoryId': self._get_category_id(metadata.category),
                },
                'status': {
                    'privacyStatus': metadata.privacy_status.value,
                    'selfDeclaredMadeForKids': False,
                }
            }
            
            # Upload video
            self.logger.info(f"Starting YouTube upload for video: {video.file_path}")
            
            # Use resumable upload for large files
            video_id = await self._resumable_upload(youtube_service, video.file_path, video_metadata)
            
            if video_id:
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                self.logger.info(f"Video uploaded successfully: {youtube_url}")
                
                # Add chapters if available
                if metadata.chapters:
                    await self._add_chapters_to_video(youtube_service, video_id, metadata.chapters)
                
                return youtube_url
            
            return None
            
        except Exception as e:
            self.logger.error(f"YouTube upload failed: {str(e)}")
            return None
    
    async def _get_youtube_service(self):
        """Get authenticated YouTube service."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            
            # Create credentials from config
            credentials = Credentials(
                token=None,
                refresh_token=self.config.youtube.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.config.youtube.client_id,
                client_secret=self.config.youtube.client_secret,
            )
            
            # Refresh the token
            credentials.refresh(Request())
            
            # Build YouTube service
            youtube = build('youtube', 'v3', credentials=credentials)
            
            return youtube
            
        except ImportError:
            self.logger.error("Google API client not installed. Install with: pip install google-api-python-client google-auth")
            return None
        except Exception as e:
            self.logger.error(f"Failed to create YouTube service: {e}")
            return None
    
    async def _resumable_upload(self, youtube_service, video_path: str, metadata: dict) -> Optional[str]:
        """Upload video using resumable upload."""
        try:
            from googleapiclient.http import MediaFileUpload
            import asyncio
            
            # Create media upload
            media = MediaFileUpload(
                video_path,
                chunksize=-1,  # Upload in single chunk for simplicity
                resumable=True,
                mimetype='video/mp4'
            )
            
            # Create upload request
            request = youtube_service.videos().insert(
                part=','.join(metadata.keys()),
                body=metadata,
                media_body=media
            )
            
            # Execute upload in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._execute_upload, request)
            
            if response and 'id' in response:
                return response['id']
            
            return None
            
        except Exception as e:
            self.logger.error(f"Resumable upload failed: {e}")
            return None
    
    def _execute_upload(self, request):
        """Execute the upload request (runs in thread pool)."""
        try:
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    self.logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Upload execution failed: {e}")
            return None
    
    def _get_category_id(self, category: str) -> str:
        """Get YouTube category ID from category name."""
        # YouTube category IDs
        categories = {
            'Education': '27',
            'Science & Technology': '28',
            'Entertainment': '24',
            'News & Politics': '25',
            'Howto & Style': '26',
            'People & Blogs': '22',
        }
        
        return categories.get(category, '27')  # Default to Education
    
    async def _add_chapters_to_video(self, youtube_service, video_id: str, chapters: list) -> None:
        """Add chapters to uploaded video."""
        try:
            if not chapters:
                return
            
            # Format chapters for YouTube description
            chapter_text = "\n\nChapters:\n"
            for chapter in chapters:
                timestamp = self._format_timestamp(chapter.start_time)
                chapter_text += f"{timestamp} - {chapter.title}\n"
            
            # Get current video details
            video_response = youtube_service.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not video_response['items']:
                return
            
            current_snippet = video_response['items'][0]['snippet']
            
            # Update description with chapters
            updated_description = current_snippet['description'] + chapter_text
            
            # Update video
            youtube_service.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': {
                        'title': current_snippet['title'],
                        'description': updated_description,
                        'categoryId': current_snippet['categoryId'],
                        'tags': current_snippet.get('tags', []),
                    }
                }
            ).execute()
            
            self.logger.info("Chapters added to YouTube video")
            
        except Exception as e:
            self.logger.warning(f"Failed to add chapters: {e}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as MM:SS or HH:MM:SS timestamp."""
        total_seconds = int(seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    async def _upload_video(self, video: VideoAsset, metadata: VideoMetadata) -> Optional[str]:
        """Upload video to YouTube."""
        try:
            # This would integrate with YouTube API
            # For now, return a mock URL
            self.logger.info("YouTube upload would happen here")
            return f"https://youtube.com/watch?v=mock_video_id"
            
        except Exception as e:
            self.logger.error(f"YouTube upload failed: {str(e)}")
            return None