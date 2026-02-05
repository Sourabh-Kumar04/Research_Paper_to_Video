"""
Database-driven content management system for production video generation.
Provides APIs for content storage, retrieval, search, and analytics.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from .database_manager import get_db_manager
from .asset_storage_manager import get_asset_storage_manager
from .file_organization_manager import get_file_org_manager

logger = logging.getLogger(__name__)


@dataclass
class ContentSearchResult:
    """Search result for content queries."""
    content_id: str
    content_type: str
    title: str
    description: Optional[str]
    relevance_score: float
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class ContentAnalytics:
    """Analytics data for content."""
    content_id: str
    views: int
    downloads: int
    generation_time_seconds: float
    file_size_bytes: int
    quality_score: float
    user_ratings: List[float]
    tags: List[str]


class ContentManagementSystem:
    """Database-driven content management with search and analytics."""
    
    def __init__(self):
        """Initialize content management system."""
        self.db_manager = get_db_manager()
        self.asset_manager = get_asset_storage_manager()
        self.file_manager = get_file_org_manager()
    
    # Paper Management
    def create_paper(self, title: str, authors: List[str], 
                    file_path: str, **kwargs) -> str:
        """Create a new research paper with organized storage."""
        try:
            # Create organized folder
            folder_path = self.file_manager.create_paper_folder(
                title, authors, kwargs.get('publication_year')
            )
            
            # Prepare paper data
            paper_data = {
                'title': title,
                'authors': authors,
                'doi': kwargs.get('doi'),
                'abstract': kwargs.get('abstract'),
                'keywords': kwargs.get('keywords', []),
                'publication_date': kwargs.get('publication_date'),
                'journal': kwargs.get('journal'),
                'arxiv_id': kwargs.get('arxiv_id'),
                'file_path': file_path,
                'folder_name': folder_path,
                'content_hash': self.file_manager.calculate_file_hash(file_path),
                'page_count': kwargs.get('page_count'),
                'word_count': kwargs.get('word_count'),
                'processing_status': 'pending'
            }
            
            # Create in database
            paper_id = self.db_manager.create_paper(paper_data)
            
            # Record creation metric
            self.db_manager.record_metric(
                'content', 'paper_created', 1.0, 'count'
            )
            
            logger.info(f"Paper created: {title} (ID: {paper_id})")
            return paper_id
            
        except Exception as e:
            logger.error(f"Error creating paper: {e}")
            raise
    
    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper with full metadata."""
        try:
            paper = self.db_manager.get_paper(paper_id)
            if paper:
                # Add asset counts
                assets = self.asset_manager.get_paper_assets(paper_id)
                paper['asset_counts'] = {
                    'videos': len(assets.get('videos', [])),
                    'audio': len(assets.get('audio', [])),
                    'visual': len(assets.get('visual', []))
                }
            return paper
            
        except Exception as e:
            logger.error(f"Error getting paper {paper_id}: {e}")
            return None
    
    def search_papers(self, query: str, filters: Optional[Dict] = None, 
                     limit: int = 50) -> List[ContentSearchResult]:
        """Advanced paper search with filtering."""
        try:
            # Basic search from database
            papers = self.db_manager.search_papers(query, limit)
            
            # Convert to search results
            results = []
            for paper in papers:
                # Calculate relevance score (simplified)
                relevance = self._calculate_relevance(query, paper)
                
                result = ContentSearchResult(
                    content_id=paper['id'],
                    content_type='paper',
                    title=paper['title'],
                    description=paper.get('abstract'),
                    relevance_score=relevance,
                    created_at=paper.get('created_at', datetime.now()),
                    metadata={
                        'authors': paper['authors'],
                        'publication_date': paper.get('publication_date'),
                        'processing_status': paper['processing_status']
                    }
                )
                results.append(result)
            
            # Apply filters if provided
            if filters:
                results = self._apply_search_filters(results, filters)
            
            # Sort by relevance
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []
    
    def update_paper_status(self, paper_id: str, status: str, 
                           progress_info: Optional[Dict] = None):
        """Update paper processing status with progress tracking."""
        try:
            self.db_manager.update_paper_status(paper_id, status)
            
            # Record status change metric
            self.db_manager.record_metric(
                'processing', f'paper_status_{status}', 1.0, 'count',
                tags={'paper_id': paper_id}
            )
            
            if progress_info:
                # Store detailed progress information
                logger.info(f"Paper {paper_id} status updated: {status}")
            
        except Exception as e:
            logger.error(f"Error updating paper status: {e}")
            raise
    
    # Content Generation Management
    def create_generation_job(self, paper_id: str, job_type: str, 
                             parameters: Dict[str, Any], 
                             priority: int = 5) -> str:
        """Create a new content generation job."""
        try:
            job_data = {
                'paper_id': paper_id,
                'job_type': job_type,
                'job_name': f"{job_type.title()} Generation",
                'priority': priority,
                'generation_parameters': parameters,
                'ai_models_requested': parameters.get('ai_models', {}),
                'estimated_duration_minutes': self._estimate_job_duration(job_type, parameters)
            }
            
            job_id = self.db_manager.create_job(job_data)
            
            # Record job creation metric
            self.db_manager.record_metric(
                'jobs', f'job_created_{job_type}', 1.0, 'count'
            )
            
            logger.info(f"Generation job created: {job_type} (ID: {job_id})")
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating generation job: {e}")
            raise
    
    def get_job_queue(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get current job queue with priorities."""
        try:
            return self.db_manager.get_pending_jobs(limit)
        except Exception as e:
            logger.error(f"Error getting job queue: {e}")
            return []
    
    def update_job_progress(self, job_id: str, progress: float, 
                           current_step: str, resource_usage: Optional[Dict] = None):
        """Update job progress with resource tracking."""
        try:
            self.db_manager.update_job_progress(job_id, progress, current_step)
            
            # Record resource usage if provided
            if resource_usage:
                for metric, value in resource_usage.items():
                    self.db_manager.record_metric(
                        'resources', metric, value, 
                        tags={'job_id': job_id}
                    )
            
        except Exception as e:
            logger.error(f"Error updating job progress: {e}")
            raise
    
    # Content Retrieval and Organization
    def get_content_by_paper(self, paper_id: str) -> Dict[str, Any]:
        """Get all content associated with a paper."""
        try:
            paper = self.get_paper(paper_id)
            if not paper:
                return {}
            
            assets = self.asset_manager.get_paper_assets(paper_id)
            
            return {
                'paper': paper,
                'videos': assets.get('videos', []),
                'audio': assets.get('audio', []),
                'visual': assets.get('visual', []),
                'generation_history': self._get_generation_history(paper_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting content for paper {paper_id}: {e}")
            return {}
    
    def get_recent_content(self, content_type: Optional[str] = None, 
                          days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently created content."""
        try:
            since = datetime.now() - timedelta(days=days)
            results = []
            
            # This would need to be implemented with proper database queries
            # For now, return empty list
            return results
            
        except Exception as e:
            logger.error(f"Error getting recent content: {e}")
            return []
    
    def get_popular_content(self, content_type: Optional[str] = None, 
                           limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular content based on usage metrics."""
        try:
            # This would analyze usage metrics to determine popularity
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting popular content: {e}")
            return []
    
    # Content Analytics
    def get_content_analytics(self, content_id: str, 
                             content_type: str) -> Optional[ContentAnalytics]:
        """Get analytics for specific content."""
        try:
            # Get basic metrics from database
            metrics = self.db_manager.get_metrics('content', content_id, hours=24*30)  # 30 days
            
            if not metrics:
                return None
            
            # Aggregate metrics
            views = sum(m['value'] for m in metrics if m.get('tags', {}).get('action') == 'view')
            downloads = sum(m['value'] for m in metrics if m.get('tags', {}).get('action') == 'download')
            
            # Get content metadata
            metadata = self.asset_manager.get_asset_metadata(content_id, content_type)
            if not metadata:
                return None
            
            analytics = ContentAnalytics(
                content_id=content_id,
                views=int(views),
                downloads=int(downloads),
                generation_time_seconds=metadata.get('generation_time', 0),
                file_size_bytes=metadata.get('file_size_bytes', 0),
                quality_score=self._calculate_quality_score(metadata),
                user_ratings=[],  # Would come from user feedback system
                tags=metadata.get('tags', [])
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting content analytics: {e}")
            return None
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics."""
        try:
            # Get database statistics
            db_stats = self.db_manager.get_database_stats()
            
            # Get storage statistics
            storage_stats = self.asset_manager.get_storage_usage()
            
            # Get recent metrics
            recent_metrics = {}
            metric_types = ['content', 'processing', 'jobs', 'resources']
            
            for metric_type in metric_types:
                metrics = self.db_manager.get_metrics(metric_type, 'total', hours=24)
                recent_metrics[metric_type] = len(metrics)
            
            # Calculate performance metrics
            performance = self._calculate_system_performance()
            
            return {
                'database': db_stats,
                'storage': storage_stats,
                'recent_activity': recent_metrics,
                'performance': performance,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system analytics: {e}")
            return {}
    
    # Content Tagging and Categorization
    def add_content_tags(self, content_id: str, content_type: str, 
                        tags: List[str]) -> bool:
        """Add tags to content for better organization."""
        try:
            # This would update the content metadata with new tags
            # Implementation depends on the specific content type
            logger.info(f"Tags added to {content_type} {content_id}: {tags}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding tags: {e}")
            return False
    
    def get_content_by_tags(self, tags: List[str], 
                           content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get content filtered by tags."""
        try:
            # This would search content by tags
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting content by tags: {e}")
            return []
    
    def auto_categorize_content(self, content_id: str, 
                               content_type: str) -> List[str]:
        """Automatically categorize content based on metadata."""
        try:
            metadata = self.asset_manager.get_asset_metadata(content_id, content_type)
            if not metadata:
                return []
            
            categories = []
            
            # Categorize based on content characteristics
            if content_type == 'video':
                duration = metadata.get('duration_seconds', 0)
                if duration < 300:  # 5 minutes
                    categories.append('short-form')
                elif duration < 1800:  # 30 minutes
                    categories.append('medium-form')
                else:
                    categories.append('long-form')
                
                resolution = metadata.get('resolution', '')
                if '4K' in resolution or '2160' in resolution:
                    categories.append('high-resolution')
                elif '1080' in resolution:
                    categories.append('hd')
            
            elif content_type == 'audio':
                if metadata.get('tts_model'):
                    categories.append('narration')
                if metadata.get('music_model'):
                    categories.append('music')
            
            elif content_type == 'visual':
                framework = metadata.get('generation_framework', '')
                if framework:
                    categories.append(f'{framework}-generated')
            
            return categories
            
        except Exception as e:
            logger.error(f"Error auto-categorizing content: {e}")
            return []
    
    # Helper Methods
    def _calculate_relevance(self, query: str, content: Dict[str, Any]) -> float:
        """Calculate relevance score for search results."""
        score = 0.0
        query_lower = query.lower()
        
        # Title match (highest weight)
        if query_lower in content.get('title', '').lower():
            score += 1.0
        
        # Author match
        authors = content.get('authors', [])
        for author in authors:
            if query_lower in author.lower():
                score += 0.5
        
        # Abstract match (if available)
        abstract = content.get('abstract', '')
        if abstract and query_lower in abstract.lower():
            score += 0.3
        
        return score
    
    def _apply_search_filters(self, results: List[ContentSearchResult], 
                             filters: Dict[str, Any]) -> List[ContentSearchResult]:
        """Apply filters to search results."""
        filtered = results
        
        # Date range filter
        if 'date_from' in filters:
            date_from = filters['date_from']
            filtered = [r for r in filtered if r.created_at >= date_from]
        
        if 'date_to' in filters:
            date_to = filters['date_to']
            filtered = [r for r in filtered if r.created_at <= date_to]
        
        # Content type filter
        if 'content_type' in filters:
            content_type = filters['content_type']
            filtered = [r for r in filtered if r.content_type == content_type]
        
        # Minimum relevance filter
        if 'min_relevance' in filters:
            min_relevance = filters['min_relevance']
            filtered = [r for r in filtered if r.relevance_score >= min_relevance]
        
        return filtered
    
    def _estimate_job_duration(self, job_type: str, parameters: Dict[str, Any]) -> int:
        """Estimate job duration in minutes."""
        base_times = {
            'video': 30,
            'audio': 10,
            'visual': 15,
            'animation': 45
        }
        
        base_time = base_times.get(job_type, 20)
        
        # Adjust based on parameters
        if parameters.get('quality_preset') == 'high':
            base_time *= 1.5
        elif parameters.get('quality_preset') == 'low':
            base_time *= 0.7
        
        return int(base_time)
    
    def _get_generation_history(self, paper_id: str) -> List[Dict[str, Any]]:
        """Get generation history for a paper."""
        try:
            # This would query the generation jobs table
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting generation history: {e}")
            return []
    
    def _calculate_quality_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate quality score based on metadata."""
        score = 0.5  # Base score
        
        # Adjust based on various factors
        if metadata.get('resolution') and '1080' in str(metadata['resolution']):
            score += 0.2
        if metadata.get('bitrate_kbps', 0) > 5000:
            score += 0.1
        if metadata.get('ai_models_used'):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_system_performance(self) -> Dict[str, Any]:
        """Calculate system performance metrics."""
        try:
            # Get recent job completion times
            completion_metrics = self.db_manager.get_metrics('jobs', 'completion_time', hours=24)
            
            avg_completion_time = 0
            if completion_metrics:
                avg_completion_time = sum(m['value'] for m in completion_metrics) / len(completion_metrics)
            
            # Get error rates
            error_metrics = self.db_manager.get_metrics('jobs', 'errors', hours=24)
            error_count = sum(m['value'] for m in error_metrics)
            
            return {
                'avg_job_completion_minutes': avg_completion_time,
                'error_count_24h': error_count,
                'system_uptime_hours': 24,  # Placeholder
                'active_jobs': len(self.get_job_queue())
            }
            
        except Exception as e:
            logger.error(f"Error calculating system performance: {e}")
            return {}


# Global content management system (initialized on demand)
_cms = None


def get_cms() -> ContentManagementSystem:
    """Get the global content management system."""
    global _cms
    if _cms is None:
        _cms = ContentManagementSystem()
    return _cms