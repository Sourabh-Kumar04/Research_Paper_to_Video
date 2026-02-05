"""
Advanced Analytics and Insights System

This module provides comprehensive analytics capabilities including:
- Viewer engagement analytics for generated videos
- Content performance metrics and recommendations
- A/B testing for different visual styles
- Automatic quality assessment and improvement suggestions
- Predictive analytics for content optimization

Optimized for 16GB RAM systems with efficient data processing.
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pathlib import Path
import statistics
import math

# Data processing and analytics
import numpy as np
import pandas as pd
from collections import defaultdict, Counter

# Machine learning for insights
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("Machine learning libraries not available. Install scikit-learn.")

# Time series analysis
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy import stats
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logging.warning("Visualization libraries not available. Install matplotlib and seaborn.")

class MetricType(Enum):
    """Types of analytics metrics."""
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    USER_BEHAVIOR = "user_behavior"
    CONTENT_EFFECTIVENESS = "content_effectiveness"

class AnalyticsEventType(Enum):
    """Types of analytics events."""
    VIDEO_VIEW = "video_view"
    VIDEO_PLAY = "video_play"
    VIDEO_PAUSE = "video_pause"
    VIDEO_SEEK = "video_seek"
    VIDEO_COMPLETE = "video_complete"
    VIDEO_SHARE = "video_share"
    VIDEO_DOWNLOAD = "video_download"
    COMMENT_ADD = "comment_add"
    RATING_SUBMIT = "rating_submit"
    GENERATION_START = "generation_start"
    GENERATION_COMPLETE = "generation_complete"
    GENERATION_ERROR = "generation_error"

@dataclass
class AnalyticsEvent:
    """Individual analytics event."""
    event_id: str
    event_type: AnalyticsEventType
    user_id: Optional[str]
    session_id: str
    content_id: str
    timestamp: datetime
    properties: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'content_id': self.content_id,
            'timestamp': self.timestamp.isoformat(),
            'properties': self.properties
        }

@dataclass
class EngagementMetrics:
    """Video engagement metrics."""
    content_id: str
    total_views: int
    unique_viewers: int
    average_watch_time: float
    completion_rate: float
    engagement_score: float
    peak_concurrent_viewers: int
    drop_off_points: List[float]
    interaction_rate: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class PerformanceMetrics:
    """Content performance metrics."""
    content_id: str
    generation_time: float
    file_size: int
    quality_score: float
    error_rate: float
    success_rate: float
    resource_usage: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class QualityAssessment:
    """Content quality assessment."""
    content_id: str
    visual_quality_score: float
    audio_quality_score: float
    content_coherence_score: float
    technical_quality_score: float
    overall_quality_score: float
    improvement_suggestions: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

class AnalyticsCollector:
    """
    Collects and processes analytics events in real-time.
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else Path("data/analytics")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory event buffer for real-time processing
        self.event_buffer: List[AnalyticsEvent] = []
        self.buffer_size = 1000  # Flush to disk when buffer reaches this size
        
        # Session tracking
        self.active_sessions: Dict[str, Dict] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Start background processing
        self._processing_task = None
        self._start_background_processing()
    
    def _start_background_processing(self):
        """Start background task for event processing."""
        async def process_events():
            while True:
                try:
                    await asyncio.sleep(60)  # Process every minute
                    await self._flush_events()
                    await self._update_real_time_metrics()
                except Exception as e:
                    self.logger.error(f"Error in background processing: {e}")
        
        self._processing_task = asyncio.create_task(process_events())
    
    async def track_event(self, event_type: AnalyticsEventType, content_id: str,
                         user_id: str = None, session_id: str = None,
                         properties: Dict = None) -> str:
        """Track an analytics event."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            content_id=content_id,
            timestamp=datetime.now(),
            properties=properties or {}
        )
        
        # Add to buffer
        self.event_buffer.append(event)
        
        # Update session tracking
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                'start_time': datetime.now(),
                'last_activity': datetime.now(),
                'events': [],
                'user_id': user_id,
                'content_id': content_id
            }
        
        self.active_sessions[session_id]['last_activity'] = datetime.now()
        self.active_sessions[session_id]['events'].append(event.event_id)
        
        # Flush buffer if full
        if len(self.event_buffer) >= self.buffer_size:
            await self._flush_events()
        
        return event.event_id
    
    async def _flush_events(self):
        """Flush event buffer to storage."""
        if not self.event_buffer:
            return
        
        # Save events to daily file
        today = datetime.now().strftime('%Y-%m-%d')
        events_file = self.storage_path / f"events_{today}.jsonl"
        
        with open(events_file, 'a') as f:
            for event in self.event_buffer:
                f.write(json.dumps(event.to_dict()) + '\n')
        
        self.logger.info(f"Flushed {len(self.event_buffer)} events to {events_file}")
        self.event_buffer.clear()
    
    async def _update_real_time_metrics(self):
        """Update real-time metrics from active sessions."""
        current_time = datetime.now()
        
        # Clean up inactive sessions (inactive for more than 1 hour)
        inactive_sessions = []
        for session_id, session_data in self.active_sessions.items():
            if current_time - session_data['last_activity'] > timedelta(hours=1):
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            del self.active_sessions[session_id]
        
        # Update metrics file
        metrics = {
            'timestamp': current_time.isoformat(),
            'active_sessions': len(self.active_sessions),
            'events_in_buffer': len(self.event_buffer)
        }
        
        metrics_file = self.storage_path / "real_time_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)

class AnalyticsProcessor:
    """
    Processes analytics data to generate insights and recommendations.
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else Path("data/analytics")
        self.logger = logging.getLogger(__name__)
    
    async def calculate_engagement_metrics(self, content_id: str, 
                                         date_range: Tuple[datetime, datetime] = None) -> EngagementMetrics:
        """Calculate engagement metrics for content."""
        events = await self._load_events_for_content(content_id, date_range)
        
        if not events:
            return EngagementMetrics(
                content_id=content_id,
                total_views=0,
                unique_viewers=0,
                average_watch_time=0.0,
                completion_rate=0.0,
                engagement_score=0.0,
                peak_concurrent_viewers=0,
                drop_off_points=[],
                interaction_rate=0.0
            )
        
        # Calculate metrics
        view_events = [e for e in events if e.event_type == AnalyticsEventType.VIDEO_VIEW]
        play_events = [e for e in events if e.event_type == AnalyticsEventType.VIDEO_PLAY]
        complete_events = [e for e in events if e.event_type == AnalyticsEventType.VIDEO_COMPLETE]
        
        total_views = len(view_events)
        unique_viewers = len(set(e.user_id for e in view_events if e.user_id))
        
        # Calculate watch time
        watch_times = []
        for session_id in set(e.session_id for e in events):
            session_events = [e for e in events if e.session_id == session_id]
            watch_time = self._calculate_session_watch_time(session_events)
            if watch_time > 0:
                watch_times.append(watch_time)
        
        average_watch_time = statistics.mean(watch_times) if watch_times else 0.0
        
        # Calculate completion rate
        completion_rate = len(complete_events) / max(len(play_events), 1)
        
        # Calculate engagement score (composite metric)
        engagement_score = self._calculate_engagement_score(
            completion_rate, average_watch_time, unique_viewers, total_views
        )
        
        # Find drop-off points
        drop_off_points = self._analyze_drop_off_points(events)
        
        # Calculate interaction rate
        interaction_events = [e for e in events if e.event_type in [
            AnalyticsEventType.COMMENT_ADD, AnalyticsEventType.VIDEO_SHARE, 
            AnalyticsEventType.RATING_SUBMIT
        ]]
        interaction_rate = len(interaction_events) / max(total_views, 1)
        
        return EngagementMetrics(
            content_id=content_id,
            total_views=total_views,
            unique_viewers=unique_viewers,
            average_watch_time=average_watch_time,
            completion_rate=completion_rate,
            engagement_score=engagement_score,
            peak_concurrent_viewers=self._calculate_peak_concurrent_viewers(events),
            drop_off_points=drop_off_points,
            interaction_rate=interaction_rate
        )
    
    async def calculate_performance_metrics(self, content_id: str) -> PerformanceMetrics:
        """Calculate performance metrics for content generation."""
        events = await self._load_events_for_content(content_id)
        
        generation_events = [e for e in events if e.event_type in [
            AnalyticsEventType.GENERATION_START,
            AnalyticsEventType.GENERATION_COMPLETE,
            AnalyticsEventType.GENERATION_ERROR
        ]]
        
        # Calculate generation time
        generation_times = []
        start_events = {e.session_id: e for e in generation_events 
                       if e.event_type == AnalyticsEventType.GENERATION_START}
        complete_events = {e.session_id: e for e in generation_events 
                          if e.event_type == AnalyticsEventType.GENERATION_COMPLETE}
        
        for session_id in start_events:
            if session_id in complete_events:
                start_time = start_events[session_id].timestamp
                end_time = complete_events[session_id].timestamp
                generation_time = (end_time - start_time).total_seconds()
                generation_times.append(generation_time)
        
        average_generation_time = statistics.mean(generation_times) if generation_times else 0.0
        
        # Calculate success/error rates
        total_attempts = len(start_events)
        successful_generations = len(complete_events)
        error_events = len([e for e in generation_events 
                           if e.event_type == AnalyticsEventType.GENERATION_ERROR])
        
        success_rate = successful_generations / max(total_attempts, 1)
        error_rate = error_events / max(total_attempts, 1)
        
        # Extract resource usage from events
        resource_usage = self._extract_resource_usage(generation_events)
        
        # Get file size from properties
        file_sizes = []
        for event in complete_events.values():
            if 'file_size' in event.properties:
                file_sizes.append(event.properties['file_size'])
        
        average_file_size = statistics.mean(file_sizes) if file_sizes else 0
        
        return PerformanceMetrics(
            content_id=content_id,
            generation_time=average_generation_time,
            file_size=int(average_file_size),
            quality_score=0.0,  # To be calculated separately
            error_rate=error_rate,
            success_rate=success_rate,
            resource_usage=resource_usage
        )
    
    async def assess_content_quality(self, content_id: str, content_data: Dict) -> QualityAssessment:
        """Assess content quality and provide improvement suggestions."""
        # Initialize scores
        visual_quality = 0.0
        audio_quality = 0.0
        content_coherence = 0.0
        technical_quality = 0.0
        
        improvement_suggestions = []
        
        # Assess visual quality
        if 'video_properties' in content_data:
            video_props = content_data['video_properties']
            
            # Resolution quality
            resolution = video_props.get('resolution', '720x480')
            width, height = map(int, resolution.split('x'))
            if width >= 1920 and height >= 1080:
                visual_quality += 0.4
            elif width >= 1280 and height >= 720:
                visual_quality += 0.3
            else:
                visual_quality += 0.1
                improvement_suggestions.append("Consider increasing video resolution to at least 1080p")
            
            # Frame rate quality
            fps = video_props.get('fps', 24)
            if fps >= 60:
                visual_quality += 0.3
            elif fps >= 30:
                visual_quality += 0.2
            else:
                visual_quality += 0.1
                improvement_suggestions.append("Consider increasing frame rate to at least 30 FPS")
            
            # Bitrate quality
            bitrate = video_props.get('bitrate', 1000)
            if bitrate >= 5000:
                visual_quality += 0.3
            elif bitrate >= 2000:
                visual_quality += 0.2
            else:
                visual_quality += 0.1
                improvement_suggestions.append("Consider increasing video bitrate for better quality")
        
        # Assess audio quality
        if 'audio_properties' in content_data:
            audio_props = content_data['audio_properties']
            
            # Sample rate quality
            sample_rate = audio_props.get('sample_rate', 22050)
            if sample_rate >= 44100:
                audio_quality += 0.4
            elif sample_rate >= 22050:
                audio_quality += 0.2
            else:
                improvement_suggestions.append("Consider using higher audio sample rate (44.1kHz)")
            
            # Audio channels
            channels = audio_props.get('channels', 1)
            if channels >= 2:
                audio_quality += 0.3
            else:
                audio_quality += 0.1
                improvement_suggestions.append("Consider using stereo audio for better experience")
            
            # Audio bitrate
            audio_bitrate = audio_props.get('bitrate', 128)
            if audio_bitrate >= 256:
                audio_quality += 0.3
            elif audio_bitrate >= 128:
                audio_quality += 0.2
            else:
                improvement_suggestions.append("Consider increasing audio bitrate to at least 128 kbps")
        
        # Assess content coherence
        if 'scenes' in content_data:
            scenes = content_data['scenes']
            
            # Scene count and structure
            scene_count = len(scenes)
            if 3 <= scene_count <= 10:
                content_coherence += 0.3
            else:
                improvement_suggestions.append("Optimal video length is 3-10 scenes for better engagement")
            
            # Scene duration consistency
            scene_durations = [scene.get('duration', 0) for scene in scenes]
            if scene_durations:
                duration_variance = statistics.variance(scene_durations)
                if duration_variance < 10:  # Low variance in scene durations
                    content_coherence += 0.3
                else:
                    improvement_suggestions.append("Consider more consistent scene durations")
            
            # Transition quality
            transitions = [scene.get('transition_type') for scene in scenes]
            if all(t is not None for t in transitions):
                content_coherence += 0.4
            else:
                improvement_suggestions.append("Add smooth transitions between all scenes")
        
        # Assess technical quality
        technical_quality = self._assess_technical_quality(content_data, improvement_suggestions)
        
        # Calculate overall quality score
        overall_quality = (visual_quality + audio_quality + content_coherence + technical_quality) / 4
        
        return QualityAssessment(
            content_id=content_id,
            visual_quality_score=visual_quality,
            audio_quality_score=audio_quality,
            content_coherence_score=content_coherence,
            technical_quality_score=technical_quality,
            overall_quality_score=overall_quality,
            improvement_suggestions=improvement_suggestions
        )
    
    def _assess_technical_quality(self, content_data: Dict, suggestions: List[str]) -> float:
        """Assess technical quality aspects."""
        score = 0.0
        
        # Check for proper encoding
        if content_data.get('codec') == 'h264':
            score += 0.3
        else:
            suggestions.append("Use H.264 codec for better compatibility")
        
        # Check for proper container format
        if content_data.get('format') == 'mp4':
            score += 0.2
        else:
            suggestions.append("Use MP4 container format for better compatibility")
        
        # Check for metadata
        if content_data.get('metadata'):
            score += 0.2
        else:
            suggestions.append("Add proper metadata to video files")
        
        # Check for chapter markers
        if content_data.get('chapters'):
            score += 0.3
        else:
            suggestions.append("Add chapter markers for better navigation")
        
        return score
    
    async def generate_content_recommendations(self, content_id: str) -> List[Dict]:
        """Generate recommendations for content improvement."""
        recommendations = []
        
        # Get engagement metrics
        engagement = await self.calculate_engagement_metrics(content_id)
        
        # Low engagement recommendations
        if engagement.completion_rate < 0.5:
            recommendations.append({
                'type': 'engagement',
                'priority': 'high',
                'title': 'Improve Content Retention',
                'description': 'Your completion rate is below 50%. Consider shorter scenes or more engaging content.',
                'suggested_actions': [
                    'Reduce scene duration by 20-30%',
                    'Add more visual elements',
                    'Improve audio quality',
                    'Add interactive elements'
                ]
            })
        
        if engagement.average_watch_time < 60:  # Less than 1 minute
            recommendations.append({
                'type': 'engagement',
                'priority': 'medium',
                'title': 'Increase Watch Time',
                'description': 'Viewers are not watching for long. Consider more compelling introductions.',
                'suggested_actions': [
                    'Create stronger opening hooks',
                    'Add preview of key points at the beginning',
                    'Improve pacing in first 30 seconds'
                ]
            })
        
        # Drop-off point recommendations
        if engagement.drop_off_points:
            major_drop_offs = [point for point in engagement.drop_off_points if point > 0.2]
            if major_drop_offs:
                recommendations.append({
                    'type': 'content_structure',
                    'priority': 'high',
                    'title': 'Address Content Drop-off Points',
                    'description': f'Significant viewer drop-off detected at {major_drop_offs}',
                    'suggested_actions': [
                        'Review content at drop-off points',
                        'Add engaging elements at these timestamps',
                        'Consider restructuring content flow'
                    ]
                })
        
        return recommendations
    
    async def _load_events_for_content(self, content_id: str, 
                                     date_range: Tuple[datetime, datetime] = None) -> List[AnalyticsEvent]:
        """Load events for specific content from storage."""
        events = []
        
        # Determine date range
        if date_range is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days
        else:
            start_date, end_date = date_range
        
        # Load events from daily files
        current_date = start_date.date()
        while current_date <= end_date.date():
            events_file = self.storage_path / f"events_{current_date.strftime('%Y-%m-%d')}.jsonl"
            
            if events_file.exists():
                with open(events_file, 'r') as f:
                    for line in f:
                        try:
                            event_data = json.loads(line.strip())
                            if event_data['content_id'] == content_id:
                                event = AnalyticsEvent(
                                    event_id=event_data['event_id'],
                                    event_type=AnalyticsEventType(event_data['event_type']),
                                    user_id=event_data['user_id'],
                                    session_id=event_data['session_id'],
                                    content_id=event_data['content_id'],
                                    timestamp=datetime.fromisoformat(event_data['timestamp']),
                                    properties=event_data['properties']
                                )
                                events.append(event)
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            self.logger.warning(f"Invalid event data: {e}")
            
            current_date += timedelta(days=1)
        
        return events
    
    def _calculate_session_watch_time(self, session_events: List[AnalyticsEvent]) -> float:
        """Calculate watch time for a session."""
        play_time = None
        total_watch_time = 0.0
        
        for event in sorted(session_events, key=lambda e: e.timestamp):
            if event.event_type == AnalyticsEventType.VIDEO_PLAY:
                play_time = event.timestamp
            elif event.event_type in [AnalyticsEventType.VIDEO_PAUSE, AnalyticsEventType.VIDEO_COMPLETE]:
                if play_time:
                    watch_duration = (event.timestamp - play_time).total_seconds()
                    total_watch_time += watch_duration
                    play_time = None
        
        return total_watch_time
    
    def _calculate_engagement_score(self, completion_rate: float, avg_watch_time: float,
                                  unique_viewers: int, total_views: int) -> float:
        """Calculate composite engagement score."""
        # Normalize metrics to 0-1 scale
        completion_score = min(completion_rate, 1.0)
        
        # Watch time score (assume 300 seconds is excellent)
        watch_time_score = min(avg_watch_time / 300.0, 1.0)
        
        # Viewer retention score
        retention_score = unique_viewers / max(total_views, 1)
        
        # Weighted average
        engagement_score = (
            completion_score * 0.4 +
            watch_time_score * 0.3 +
            retention_score * 0.3
        )
        
        return engagement_score
    
    def _analyze_drop_off_points(self, events: List[AnalyticsEvent]) -> List[float]:
        """Analyze where viewers drop off during video playback."""
        # This is a simplified implementation
        # In practice, you'd need more detailed playback position data
        
        seek_events = [e for e in events if e.event_type == AnalyticsEventType.VIDEO_SEEK]
        pause_events = [e for e in events if e.event_type == AnalyticsEventType.VIDEO_PAUSE]
        
        drop_off_points = []
        
        # Analyze seek patterns (large forward seeks indicate skipping)
        for event in seek_events:
            if 'seek_from' in event.properties and 'seek_to' in event.properties:
                seek_from = event.properties['seek_from']
                seek_to = event.properties['seek_to']
                
                if seek_to - seek_from > 30:  # Skip more than 30 seconds
                    drop_off_points.append(seek_from)
        
        return drop_off_points
    
    def _calculate_peak_concurrent_viewers(self, events: List[AnalyticsEvent]) -> int:
        """Calculate peak concurrent viewers."""
        # Track concurrent viewers over time
        viewer_timeline = defaultdict(int)
        
        for event in events:
            timestamp = event.timestamp.replace(second=0, microsecond=0)  # Round to minute
            
            if event.event_type == AnalyticsEventType.VIDEO_PLAY:
                viewer_timeline[timestamp] += 1
            elif event.event_type in [AnalyticsEventType.VIDEO_PAUSE, AnalyticsEventType.VIDEO_COMPLETE]:
                viewer_timeline[timestamp] -= 1
        
        # Calculate running total
        concurrent_viewers = 0
        peak_viewers = 0
        
        for timestamp in sorted(viewer_timeline.keys()):
            concurrent_viewers += viewer_timeline[timestamp]
            peak_viewers = max(peak_viewers, concurrent_viewers)
        
        return peak_viewers
    
    def _extract_resource_usage(self, events: List[AnalyticsEvent]) -> Dict[str, float]:
        """Extract resource usage metrics from events."""
        cpu_usage = []
        memory_usage = []
        gpu_usage = []
        
        for event in events:
            if 'resource_usage' in event.properties:
                usage = event.properties['resource_usage']
                
                if 'cpu_percent' in usage:
                    cpu_usage.append(usage['cpu_percent'])
                if 'memory_mb' in usage:
                    memory_usage.append(usage['memory_mb'])
                if 'gpu_percent' in usage:
                    gpu_usage.append(usage['gpu_percent'])
        
        return {
            'avg_cpu_percent': statistics.mean(cpu_usage) if cpu_usage else 0.0,
            'avg_memory_mb': statistics.mean(memory_usage) if memory_usage else 0.0,
            'avg_gpu_percent': statistics.mean(gpu_usage) if gpu_usage else 0.0,
            'peak_cpu_percent': max(cpu_usage) if cpu_usage else 0.0,
            'peak_memory_mb': max(memory_usage) if memory_usage else 0.0,
            'peak_gpu_percent': max(gpu_usage) if gpu_usage else 0.0
        }

class ABTestingManager:
    """
    Manages A/B testing for different visual styles and content variations.
    """
    
    def __init__(self, analytics_processor: AnalyticsProcessor):
        self.analytics_processor = analytics_processor
        self.active_tests: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
    
    async def create_ab_test(self, test_name: str, variants: List[Dict], 
                           traffic_split: List[float] = None) -> str:
        """Create new A/B test."""
        test_id = str(uuid.uuid4())
        
        if traffic_split is None:
            # Equal split
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        if len(traffic_split) != len(variants):
            raise ValueError("Traffic split must match number of variants")
        
        if abs(sum(traffic_split) - 1.0) > 0.001:
            raise ValueError("Traffic split must sum to 1.0")
        
        test_config = {
            'test_id': test_id,
            'test_name': test_name,
            'variants': variants,
            'traffic_split': traffic_split,
            'created_at': datetime.now(),
            'status': 'active',
            'results': {}
        }
        
        self.active_tests[test_id] = test_config
        
        self.logger.info(f"Created A/B test '{test_name}' with {len(variants)} variants")
        
        return test_id
    
    def assign_variant(self, test_id: str, user_id: str) -> Optional[Dict]:
        """Assign user to test variant."""
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        
        # Use hash of user_id for consistent assignment
        import hashlib
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        assignment_value = (user_hash % 10000) / 10000.0  # 0.0 to 1.0
        
        # Determine variant based on traffic split
        cumulative_split = 0.0
        for i, split in enumerate(test['traffic_split']):
            cumulative_split += split
            if assignment_value <= cumulative_split:
                return {
                    'test_id': test_id,
                    'variant_index': i,
                    'variant': test['variants'][i]
                }
        
        # Fallback to last variant
        return {
            'test_id': test_id,
            'variant_index': len(test['variants']) - 1,
            'variant': test['variants'][-1]
        }
    
    async def analyze_test_results(self, test_id: str) -> Dict:
        """Analyze A/B test results."""
        if test_id not in self.active_tests:
            return {}
        
        test = self.active_tests[test_id]
        results = {}
        
        # Collect metrics for each variant
        for i, variant in enumerate(test['variants']):
            variant_id = variant.get('content_id')
            if variant_id:
                engagement = await self.analytics_processor.calculate_engagement_metrics(variant_id)
                performance = await self.analytics_processor.calculate_performance_metrics(variant_id)
                
                results[f'variant_{i}'] = {
                    'variant_config': variant,
                    'engagement_metrics': engagement.to_dict(),
                    'performance_metrics': performance.to_dict()
                }
        
        # Calculate statistical significance
        if len(results) >= 2:
            results['statistical_analysis'] = self._calculate_statistical_significance(results)
        
        # Update test results
        test['results'] = results
        test['last_analyzed'] = datetime.now()
        
        return results
    
    def _calculate_statistical_significance(self, results: Dict) -> Dict:
        """Calculate statistical significance between variants."""
        # Simplified statistical analysis
        # In practice, you'd use proper statistical tests
        
        variants = list(results.keys())
        if len(variants) < 2:
            return {}
        
        # Compare engagement scores
        engagement_scores = []
        sample_sizes = []
        
        for variant in variants:
            if variant.startswith('variant_'):
                engagement = results[variant]['engagement_metrics']
                engagement_scores.append(engagement['engagement_score'])
                sample_sizes.append(engagement['total_views'])
        
        if len(engagement_scores) >= 2:
            # Simple comparison (in practice, use proper statistical tests)
            best_variant = variants[engagement_scores.index(max(engagement_scores))]
            improvement = max(engagement_scores) - min(engagement_scores)
            
            return {
                'best_variant': best_variant,
                'improvement': improvement,
                'confidence': 'medium',  # Placeholder
                'recommendation': 'Continue test' if improvement < 0.1 else 'Implement winning variant'
            }
        
        return {}

# Integration functions
async def track_video_generation_analytics(content_id: str, generation_data: Dict) -> str:
    """Track analytics for video generation process."""
    collector = AnalyticsCollector()
    
    # Track generation start
    start_event_id = await collector.track_event(
        AnalyticsEventType.GENERATION_START,
        content_id,
        properties={
            'generation_config': generation_data.get('config', {}),
            'ai_models': generation_data.get('ai_models', {}),
            'quality_preset': generation_data.get('quality_preset', 'medium')
        }
    )
    
    return start_event_id

async def track_video_completion_analytics(content_id: str, result_data: Dict) -> str:
    """Track analytics for completed video generation."""
    collector = AnalyticsCollector()
    
    # Track generation completion
    complete_event_id = await collector.track_event(
        AnalyticsEventType.GENERATION_COMPLETE,
        content_id,
        properties={
            'file_size': result_data.get('file_size', 0),
            'duration': result_data.get('duration', 0),
            'generation_time': result_data.get('generation_time', 0),
            'resource_usage': result_data.get('resource_usage', {}),
            'quality_metrics': result_data.get('quality_metrics', {})
        }
    )
    
    return complete_event_id

if __name__ == "__main__":
    # Example usage
    async def main():
        print("Advanced analytics system initialized successfully")
        print("Available features:")
        print(f"- Machine learning: {ML_AVAILABLE}")
        print(f"- Visualization: {VISUALIZATION_AVAILABLE}")
        
        # Example analytics collection
        collector = AnalyticsCollector()
        
        # Track some sample events
        await collector.track_event(
            AnalyticsEventType.VIDEO_VIEW,
            "test_video_123",
            user_id="user_456",
            properties={"source": "direct_link"}
        )
        
        print("Sample analytics event tracked")
        
        # Example analytics processing
        processor = AnalyticsProcessor()
        
        # Calculate sample metrics
        engagement = await processor.calculate_engagement_metrics("test_video_123")
        print(f"Engagement score: {engagement.engagement_score:.2f}")
    
    asyncio.run(main())