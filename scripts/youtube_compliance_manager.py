"""
YouTube compliance and metadata manager for production video generation.
Ensures all generated videos meet YouTube specifications and requirements.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re
import subprocess

logger = logging.getLogger(__name__)


class YouTubeComplianceManager:
    """Manages YouTube compliance and metadata for generated videos."""
    
    def __init__(self):
        """Initialize YouTube compliance manager."""
        self.youtube_specs = self._load_youtube_specifications()
        self.metadata_templates = self._load_metadata_templates()
    
    def _load_youtube_specifications(self) -> Dict[str, Any]:
        """Load YouTube technical specifications."""
        return {
            'video': {
                'aspect_ratios': {
                    'recommended': '16:9',
                    'supported': ['16:9', '4:3', '1:1', '9:16']
                },
                'resolutions': {
                    'recommended': ['1920x1080', '1280x720'],
                    'supported': [
                        '426x240', '640x360', '854x480', '1280x720',
                        '1920x1080', '2560x1440', '3840x2160'
                    ]
                },
                'frame_rates': {
                    'recommended': [24, 25, 30, 50, 60],
                    'supported': list(range(24, 61))
                },
                'codecs': {
                    'recommended': ['H.264', 'H.265'],
                    'supported': ['H.264', 'H.265', 'VP9', 'AV1']
                },
                'bitrates': {
                    '1080p': {'sdr': 8000, 'hdr': 10000},
                    '720p': {'sdr': 5000, 'hdr': 6500},
                    '480p': {'sdr': 2500, 'hdr': 4000},
                    '360p': {'sdr': 1000, 'hdr': 1500}
                },
                'file_size': {
                    'max_bytes': 128 * 1024 * 1024 * 1024,  # 128GB
                    'max_duration_seconds': 12 * 60 * 60  # 12 hours
                }
            },
            'audio': {
                'codecs': {
                    'recommended': ['AAC-LC'],
                    'supported': ['AAC-LC', 'MP3']
                },
                'sample_rates': {
                    'recommended': [48000],
                    'supported': [22050, 44100, 48000, 96000]
                },
                'bitrates': {
                    'mono': 128,
                    'stereo': 384,
                    'surround': 512
                },
                'channels': {
                    'recommended': 2,
                    'supported': [1, 2, 6, 8]
                }
            },
            'metadata': {
                'title': {
                    'max_length': 100,
                    'required': True
                },
                'description': {
                    'max_length': 5000,
                    'required': False
                },
                'tags': {
                    'max_count': 500,
                    'max_length_per_tag': 30,
                    'required': False
                },
                'thumbnail': {
                    'formats': ['JPG', 'GIF', 'PNG'],
                    'max_size_bytes': 2 * 1024 * 1024,  # 2MB
                    'min_resolution': '640x360',
                    'aspect_ratio': '16:9'
                }
            }
        }
    
    def _load_metadata_templates(self) -> Dict[str, str]:
        """Load metadata templates for different content types."""
        return {
            'research_paper': {
                'title_template': "{paper_title} - AI Generated Video Summary",
                'description_template': """
This video provides an AI-generated summary of the research paper: "{paper_title}"

Authors: {authors}
{doi_info}

Key Topics:
{keywords}

Abstract:
{abstract}

Generated using advanced AI models including:
{ai_models}

Timestamps:
{chapters}

#Research #AI #MachineLearning #Science #Education
                """.strip(),
                'tags': [
                    'research', 'AI', 'machine learning', 'science', 'education',
                    'academic', 'paper summary', 'artificial intelligence'
                ]
            },
            'tutorial': {
                'title_template': "{topic} - Complete Tutorial",
                'description_template': """
Complete tutorial on {topic}

What you'll learn:
{learning_objectives}

Timestamps:
{chapters}

Resources mentioned:
{resources}

#Tutorial #Education #Learning #HowTo
                """.strip(),
                'tags': [
                    'tutorial', 'education', 'learning', 'how-to', 'guide'
                ]
            },
            'explanation': {
                'title_template': "{concept} Explained",
                'description_template': """
Detailed explanation of {concept}

Key concepts covered:
{key_concepts}

Timestamps:
{chapters}

#Explanation #Education #Concept #Learning
                """.strip(),
                'tags': [
                    'explanation', 'education', 'concept', 'learning'
                ]
            }
        }
    
    def validate_video_compliance(self, video_path: str) -> Dict[str, Any]:
        """Validate video file against YouTube specifications."""
        try:
            # Get video information using FFprobe
            video_info = self._get_video_info(video_path)
            
            compliance_report = {
                'compliant': True,
                'issues': [],
                'warnings': [],
                'recommendations': [],
                'video_info': video_info
            }
            
            # Check aspect ratio
            aspect_ratio = self._calculate_aspect_ratio(
                video_info['width'], video_info['height']
            )
            
            if aspect_ratio not in self.youtube_specs['video']['aspect_ratios']['supported']:
                compliance_report['issues'].append(
                    f"Unsupported aspect ratio: {aspect_ratio}. "
                    f"Recommended: {self.youtube_specs['video']['aspect_ratios']['recommended']}"
                )
                compliance_report['compliant'] = False
            elif aspect_ratio != self.youtube_specs['video']['aspect_ratios']['recommended']:
                compliance_report['warnings'].append(
                    f"Non-recommended aspect ratio: {aspect_ratio}. "
                    f"Recommended: {self.youtube_specs['video']['aspect_ratios']['recommended']}"
                )
            
            # Check resolution
            resolution = f"{video_info['width']}x{video_info['height']}"
            if resolution not in self.youtube_specs['video']['resolutions']['supported']:
                compliance_report['issues'].append(
                    f"Unsupported resolution: {resolution}"
                )
                compliance_report['compliant'] = False
            elif resolution not in self.youtube_specs['video']['resolutions']['recommended']:
                compliance_report['recommendations'].append(
                    f"Consider using recommended resolution: "
                    f"{', '.join(self.youtube_specs['video']['resolutions']['recommended'])}"
                )
            
            # Check frame rate
            fps = video_info.get('fps', 0)
            if fps not in self.youtube_specs['video']['frame_rates']['supported']:
                compliance_report['issues'].append(
                    f"Unsupported frame rate: {fps}fps"
                )
                compliance_report['compliant'] = False
            elif fps not in self.youtube_specs['video']['frame_rates']['recommended']:
                compliance_report['warnings'].append(
                    f"Non-recommended frame rate: {fps}fps"
                )
            
            # Check codec
            codec = video_info.get('codec', '').upper()
            if codec not in [c.upper() for c in self.youtube_specs['video']['codecs']['supported']]:
                compliance_report['issues'].append(
                    f"Unsupported video codec: {codec}"
                )
                compliance_report['compliant'] = False
            elif codec not in [c.upper() for c in self.youtube_specs['video']['codecs']['recommended']]:
                compliance_report['recommendations'].append(
                    f"Consider using recommended codec: "
                    f"{', '.join(self.youtube_specs['video']['codecs']['recommended'])}"
                )
            
            # Check file size
            file_size = os.path.getsize(video_path)
            max_size = self.youtube_specs['video']['file_size']['max_bytes']
            if file_size > max_size:
                compliance_report['issues'].append(
                    f"File size exceeds YouTube limit: {file_size / (1024**3):.2f}GB > "
                    f"{max_size / (1024**3):.0f}GB"
                )
                compliance_report['compliant'] = False
            
            # Check duration
            duration = video_info.get('duration', 0)
            max_duration = self.youtube_specs['video']['file_size']['max_duration_seconds']
            if duration > max_duration:
                compliance_report['issues'].append(
                    f"Duration exceeds YouTube limit: {duration/3600:.2f}h > {max_duration/3600:.0f}h"
                )
                compliance_report['compliant'] = False
            
            # Check audio compliance
            audio_compliance = self._validate_audio_compliance(video_info)
            compliance_report['issues'].extend(audio_compliance['issues'])
            compliance_report['warnings'].extend(audio_compliance['warnings'])
            compliance_report['recommendations'].extend(audio_compliance['recommendations'])
            
            if audio_compliance['issues']:
                compliance_report['compliant'] = False
            
            return compliance_report
            
        except Exception as e:
            logger.error(f"Error validating video compliance: {e}")
            return {
                'compliant': False,
                'issues': [f"Validation error: {str(e)}"],
                'warnings': [],
                'recommendations': [],
                'video_info': {}
            }
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using FFprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(result.stdout)
            
            video_stream = None
            audio_stream = None
            
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video' and video_stream is None:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and audio_stream is None:
                    audio_stream = stream
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            # Calculate FPS
            fps = 0
            if 'r_frame_rate' in video_stream:
                fps_parts = video_stream['r_frame_rate'].split('/')
                if len(fps_parts) == 2 and int(fps_parts[1]) != 0:
                    fps = int(fps_parts[0]) / int(fps_parts[1])
            
            return {
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': round(fps),
                'duration': float(probe_data.get('format', {}).get('duration', 0)),
                'codec': video_stream.get('codec_name', ''),
                'bitrate': int(probe_data.get('format', {}).get('bit_rate', 0)),
                'audio_codec': audio_stream.get('codec_name', '') if audio_stream else '',
                'audio_sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream else 0,
                'audio_channels': int(audio_stream.get('channels', 0)) if audio_stream else 0,
                'audio_bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream else 0
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {e}")
            raise ValueError(f"Could not analyze video file: {e}")
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
    
    def _validate_audio_compliance(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate audio compliance."""
        compliance = {
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        audio_codec = video_info.get('audio_codec', '').upper()
        if audio_codec:
            # Check audio codec
            if audio_codec not in [c.upper() for c in self.youtube_specs['audio']['codecs']['supported']]:
                compliance['issues'].append(f"Unsupported audio codec: {audio_codec}")
            elif audio_codec not in [c.upper() for c in self.youtube_specs['audio']['codecs']['recommended']]:
                compliance['recommendations'].append(
                    f"Consider using recommended audio codec: "
                    f"{', '.join(self.youtube_specs['audio']['codecs']['recommended'])}"
                )
            
            # Check sample rate
            sample_rate = video_info.get('audio_sample_rate', 0)
            if sample_rate not in self.youtube_specs['audio']['sample_rates']['supported']:
                compliance['issues'].append(f"Unsupported audio sample rate: {sample_rate}Hz")
            elif sample_rate not in self.youtube_specs['audio']['sample_rates']['recommended']:
                compliance['recommendations'].append(
                    f"Consider using recommended sample rate: "
                    f"{', '.join(map(str, self.youtube_specs['audio']['sample_rates']['recommended']))}Hz"
                )
            
            # Check channels
            channels = video_info.get('audio_channels', 0)
            if channels not in self.youtube_specs['audio']['channels']['supported']:
                compliance['issues'].append(f"Unsupported audio channels: {channels}")
            elif channels != self.youtube_specs['audio']['channels']['recommended']:
                compliance['recommendations'].append(
                    f"Consider using recommended channel count: "
                    f"{self.youtube_specs['audio']['channels']['recommended']}"
                )
        
        return compliance
    
    def _calculate_aspect_ratio(self, width: int, height: int) -> str:
        """Calculate aspect ratio from width and height."""
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        
        divisor = gcd(width, height)
        ratio_w = width // divisor
        ratio_h = height // divisor
        
        return f"{ratio_w}:{ratio_h}"
    
    def generate_metadata(self, content_type: str, content_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate YouTube-compliant metadata."""
        try:
            template = self.metadata_templates.get(content_type, self.metadata_templates['research_paper'])
            
            # Generate title
            title = template['title_template'].format(**content_info)
            title = self._sanitize_title(title)
            
            # Generate description
            description = template['description_template'].format(**content_info)
            description = self._sanitize_description(description)
            
            # Generate tags
            tags = template['tags'].copy()
            if 'keywords' in content_info and content_info['keywords']:
                tags.extend(content_info['keywords'][:10])  # Add up to 10 keywords
            
            tags = self._sanitize_tags(tags)
            
            # Generate chapters if available
            chapters = self._generate_chapters(content_info.get('scenes', []))
            
            return {
                'title': title,
                'description': description,
                'tags': tags,
                'chapters': chapters,
                'category': self._determine_category(content_type),
                'language': content_info.get('language', 'en'),
                'privacy': content_info.get('privacy', 'public'),
                'license': content_info.get('license', 'youtube')
            }
            
        except Exception as e:
            logger.error(f"Error generating metadata: {e}")
            return self._get_default_metadata()
    
    def _sanitize_title(self, title: str) -> str:
        """Sanitize title for YouTube compliance."""
        # Remove problematic characters
        title = re.sub(r'[<>]', '', title)
        
        # Limit length
        max_length = self.youtube_specs['metadata']['title']['max_length']
        if len(title) > max_length:
            title = title[:max_length-3] + '...'
        
        return title.strip()
    
    def _sanitize_description(self, description: str) -> str:
        """Sanitize description for YouTube compliance."""
        # Remove excessive whitespace
        description = re.sub(r'\n\s*\n', '\n\n', description)
        description = re.sub(r' +', ' ', description)
        
        # Limit length
        max_length = self.youtube_specs['metadata']['description']['max_length']
        if len(description) > max_length:
            description = description[:max_length-3] + '...'
        
        return description.strip()
    
    def _sanitize_tags(self, tags: List[str]) -> List[str]:
        """Sanitize tags for YouTube compliance."""
        sanitized_tags = []
        max_count = self.youtube_specs['metadata']['tags']['max_count']
        max_length = self.youtube_specs['metadata']['tags']['max_length_per_tag']
        
        for tag in tags:
            # Clean tag
            tag = re.sub(r'[^\w\s-]', '', tag).strip().lower()
            
            # Skip empty or too long tags
            if not tag or len(tag) > max_length:
                continue
            
            # Avoid duplicates
            if tag not in sanitized_tags:
                sanitized_tags.append(tag)
            
            # Respect count limit
            if len(sanitized_tags) >= max_count:
                break
        
        return sanitized_tags
    
    def _generate_chapters(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate chapter markers from scenes."""
        chapters = []
        
        for i, scene in enumerate(scenes):
            start_time = scene.get('start_time', i * 30)  # Default 30s per scene
            title = scene.get('title', f"Scene {i+1}")
            
            chapters.append({
                'time': self._format_timestamp(start_time),
                'title': title[:100]  # YouTube chapter title limit
            })
        
        return chapters
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp for YouTube chapters."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def _determine_category(self, content_type: str) -> str:
        """Determine YouTube category based on content type."""
        category_mapping = {
            'research_paper': 'Education',
            'tutorial': 'Education',
            'explanation': 'Education',
            'entertainment': 'Entertainment',
            'news': 'News & Politics',
            'technology': 'Science & Technology'
        }
        
        return category_mapping.get(content_type, 'Education')
    
    def _get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata for fallback."""
        return {
            'title': 'AI Generated Video',
            'description': 'This video was generated using AI technology.',
            'tags': ['AI', 'generated', 'video'],
            'chapters': [],
            'category': 'Education',
            'language': 'en',
            'privacy': 'public',
            'license': 'youtube'
        }
    
    def create_thumbnail(self, video_path: str, output_path: str, 
                        timestamp: float = None) -> bool:
        """Create YouTube-compliant thumbnail from video."""
        try:
            if timestamp is None:
                # Use middle of video
                video_info = self._get_video_info(video_path)
                timestamp = video_info['duration'] / 2
            
            # Extract frame using FFmpeg
            cmd = [
                'ffmpeg', '-i', video_path, '-ss', str(timestamp),
                '-vframes', '1', '-q:v', '2', '-y', output_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Validate thumbnail compliance
            return self._validate_thumbnail(output_path)
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return False
    
    def _validate_thumbnail(self, thumbnail_path: str) -> bool:
        """Validate thumbnail against YouTube specifications."""
        try:
            from PIL import Image
            
            with Image.open(thumbnail_path) as img:
                width, height = img.size
                file_size = os.path.getsize(thumbnail_path)
                
                # Check format
                if img.format not in self.youtube_specs['metadata']['thumbnail']['formats']:
                    logger.warning(f"Thumbnail format {img.format} not recommended")
                
                # Check size
                max_size = self.youtube_specs['metadata']['thumbnail']['max_size_bytes']
                if file_size > max_size:
                    logger.error(f"Thumbnail too large: {file_size} > {max_size}")
                    return False
                
                # Check resolution
                if width < 640 or height < 360:
                    logger.error(f"Thumbnail resolution too low: {width}x{height}")
                    return False
                
                # Check aspect ratio
                aspect_ratio = self._calculate_aspect_ratio(width, height)
                if aspect_ratio != '16:9':
                    logger.warning(f"Thumbnail aspect ratio not optimal: {aspect_ratio}")
                
                return True
                
        except ImportError:
            logger.warning("PIL not available for thumbnail validation")
            return True  # Assume valid if we can't check
        except Exception as e:
            logger.error(f"Error validating thumbnail: {e}")
            return False
    
    def export_metadata_json(self, metadata: Dict[str, Any], output_path: str):
        """Export metadata to JSON file for upload tools."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Metadata exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting metadata: {e}")
            raise
    
    def get_upload_recommendations(self, video_path: str) -> Dict[str, Any]:
        """Get recommendations for YouTube upload."""
        compliance = self.validate_video_compliance(video_path)
        
        recommendations = {
            'upload_ready': compliance['compliant'],
            'required_fixes': compliance['issues'],
            'suggested_improvements': compliance['warnings'] + compliance['recommendations'],
            'optimal_upload_settings': {
                'processing_quality': 'HD' if compliance['video_info'].get('height', 0) >= 720 else 'SD',
                'recommended_bitrate': self._get_recommended_bitrate(compliance['video_info']),
                'upload_time': 'off-peak hours for faster processing',
                'thumbnail_required': True,
                'end_screen_recommended': True,
                'cards_recommended': True
            }
        }
        
        return recommendations
    
    def _get_recommended_bitrate(self, video_info: Dict[str, Any]) -> str:
        """Get recommended bitrate based on resolution."""
        height = video_info.get('height', 0)
        
        if height >= 1080:
            return "8-10 Mbps for 1080p"
        elif height >= 720:
            return "5-6 Mbps for 720p"
        elif height >= 480:
            return "2.5-4 Mbps for 480p"
        else:
            return "1-1.5 Mbps for 360p"


# Global YouTube compliance manager
youtube_compliance_manager = YouTubeComplianceManager()


def get_youtube_compliance_manager() -> YouTubeComplianceManager:
    """Get the global YouTube compliance manager."""
    return youtube_compliance_manager