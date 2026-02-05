"""
Database manager for production video generation system.
Handles PostgreSQL connections, migrations, and CRUD operations.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from .database_schema import (
    Base, ResearchPaper, GeneratedVideo, VideoScene, AudioAsset,
    VisualAsset, ContentVersion, GenerationJob, SystemMetrics
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager with connection URL."""
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or use default."""
        # Try environment variables first
        if 'DATABASE_URL' in os.environ:
            return os.environ['DATABASE_URL']
        
        # Build from individual components
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'video_generation')
        username = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'postgres')
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _setup_engine(self):
        """Set up SQLAlchemy engine with optimized settings."""
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_database_if_not_exists(self):
        """Create database if it doesn't exist."""
        try:
            # Skip for SQLite (database is created automatically)
            if 'sqlite' in self.database_url.lower():
                logger.info("Using SQLite database - no need to create database")
                return
            
            if not PSYCOPG2_AVAILABLE:
                logger.warning("psycopg2 not available - skipping database creation")
                return
            
            # Parse database URL to get connection info
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            # Connect to postgres database to create our database
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            database_name = parsed.path.lstrip('/')
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (database_name,)
            )
            
            if not cursor.fetchone():
                cursor.execute(f'CREATE DATABASE "{database_name}"')
                logger.info(f"Created database: {database_name}")
            else:
                logger.info(f"Database already exists: {database_name}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    # Research Paper operations
    def create_paper(self, paper_data: Dict[str, Any]) -> str:
        """Create a new research paper record."""
        with self.get_session() as session:
            paper = ResearchPaper(**paper_data)
            session.add(paper)
            session.flush()
            return str(paper.id)
    
    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get research paper by ID."""
        with self.get_session() as session:
            paper = session.query(ResearchPaper).filter(
                ResearchPaper.id == paper_id
            ).first()
            
            if paper:
                return {
                    'id': str(paper.id),
                    'title': paper.title,
                    'authors': paper.authors,
                    'doi': paper.doi,
                    'abstract': paper.abstract,
                    'keywords': paper.keywords,
                    'publication_date': paper.publication_date,
                    'journal': paper.journal,
                    'arxiv_id': paper.arxiv_id,
                    'file_path': paper.file_path,
                    'folder_name': paper.folder_name,
                    'processing_status': paper.processing_status,
                    'created_at': paper.created_at,
                    'updated_at': paper.updated_at
                }
            return None
    
    def search_papers(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search papers by title, authors, or keywords."""
        with self.get_session() as session:
            # Use different search strategies based on database type
            if 'sqlite' in self.database_url.lower():
                # For SQLite, search in JSON fields using LIKE
                papers = session.query(ResearchPaper).filter(
                    ResearchPaper.title.ilike(f'%{query}%') |
                    ResearchPaper.abstract.ilike(f'%{query}%') |
                    ResearchPaper.authors.ilike(f'%{query}%') |
                    ResearchPaper.keywords.ilike(f'%{query}%')
                ).limit(limit).all()
            else:
                # For PostgreSQL, use proper array operations
                papers = session.query(ResearchPaper).filter(
                    ResearchPaper.title.ilike(f'%{query}%') |
                    ResearchPaper.abstract.ilike(f'%{query}%') |
                    ResearchPaper.keywords.any(query)
                ).limit(limit).all()
            
            return [
                {
                    'id': str(paper.id),
                    'title': paper.title,
                    'authors': paper.authors,
                    'publication_date': paper.publication_date,
                    'processing_status': paper.processing_status
                }
                for paper in papers
            ]
    
    def update_paper_status(self, paper_id: str, status: str):
        """Update paper processing status."""
        with self.get_session() as session:
            session.query(ResearchPaper).filter(
                ResearchPaper.id == paper_id
            ).update({'processing_status': status})
    
    # Video operations
    def create_video(self, video_data: Dict[str, Any]) -> str:
        """Create a new generated video record."""
        with self.get_session() as session:
            video = GeneratedVideo(**video_data)
            session.add(video)
            session.flush()
            return str(video.id)
    
    def get_videos_by_paper(self, paper_id: str) -> List[Dict[str, Any]]:
        """Get all videos for a paper."""
        with self.get_session() as session:
            videos = session.query(GeneratedVideo).filter(
                GeneratedVideo.paper_id == paper_id
            ).all()
            
            return [
                {
                    'id': str(video.id),
                    'title': video.title,
                    'duration_seconds': video.duration_seconds,
                    'resolution': video.resolution,
                    'status': video.status,
                    'is_published': video.is_published,
                    'created_at': video.created_at
                }
                for video in videos
            ]
    
    def update_video_status(self, video_id: str, status: str, 
                           completed_at: Optional[Any] = None):
        """Update video generation status."""
        with self.get_session() as session:
            update_data = {'status': status}
            if completed_at:
                update_data['generation_completed_at'] = completed_at
            
            session.query(GeneratedVideo).filter(
                GeneratedVideo.id == video_id
            ).update(update_data)
    
    # Job operations
    def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new generation job."""
        with self.get_session() as session:
            job = GenerationJob(**job_data)
            session.add(job)
            session.flush()
            return str(job.id)
    
    def get_pending_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending jobs ordered by priority."""
        with self.get_session() as session:
            jobs = session.query(GenerationJob).filter(
                GenerationJob.status.in_(['queued', 'running'])
            ).order_by(
                GenerationJob.priority.desc(),
                GenerationJob.created_at.asc()
            ).limit(limit).all()
            
            return [
                {
                    'id': str(job.id),
                    'paper_id': str(job.paper_id),
                    'job_type': job.job_type,
                    'job_name': job.job_name,
                    'priority': job.priority,
                    'status': job.status,
                    'progress_percentage': job.progress_percentage,
                    'created_at': job.created_at
                }
                for job in jobs
            ]
    
    def update_job_progress(self, job_id: str, progress: float, 
                           current_step: Optional[str] = None):
        """Update job progress."""
        with self.get_session() as session:
            update_data = {'progress_percentage': progress}
            if current_step:
                update_data['current_step'] = current_step
            
            session.query(GenerationJob).filter(
                GenerationJob.id == job_id
            ).update(update_data)
    
    # Asset operations
    def create_audio_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create a new audio asset record."""
        with self.get_session() as session:
            asset = AudioAsset(**asset_data)
            session.add(asset)
            session.flush()
            return str(asset.id)
    
    def create_visual_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create a new visual asset record."""
        with self.get_session() as session:
            asset = VisualAsset(**asset_data)
            session.add(asset)
            session.flush()
            return str(asset.id)
    
    def get_assets_by_paper(self, paper_id: str, 
                           asset_type: Optional[str] = None) -> Dict[str, List]:
        """Get all assets for a paper, optionally filtered by type."""
        with self.get_session() as session:
            # Get audio assets
            audio_query = session.query(AudioAsset).filter(
                AudioAsset.paper_id == paper_id
            )
            if asset_type:
                audio_query = audio_query.filter(AudioAsset.asset_type == asset_type)
            audio_assets = audio_query.all()
            
            # Get visual assets
            visual_query = session.query(VisualAsset).filter(
                VisualAsset.paper_id == paper_id
            )
            if asset_type:
                visual_query = visual_query.filter(VisualAsset.asset_type == asset_type)
            visual_assets = visual_query.all()
            
            return {
                'audio': [
                    {
                        'id': str(asset.id),
                        'asset_type': asset.asset_type,
                        'title': asset.title,
                        'duration_seconds': asset.duration_seconds,
                        'file_path': asset.file_path,
                        'tts_model': asset.tts_model,
                        'created_at': asset.created_at
                    }
                    for asset in audio_assets
                ],
                'visual': [
                    {
                        'id': str(asset.id),
                        'asset_type': asset.asset_type,
                        'title': asset.title,
                        'width': asset.width,
                        'height': asset.height,
                        'file_path': asset.file_path,
                        'generation_framework': asset.generation_framework,
                        'created_at': asset.created_at
                    }
                    for asset in visual_assets
                ]
            }
    
    # Metrics operations
    def record_metric(self, metric_type: str, metric_name: str, 
                     value: float, unit: Optional[str] = None, 
                     tags: Optional[Dict] = None):
        """Record a system metric."""
        with self.get_session() as session:
            metric = SystemMetrics(
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                unit=unit,
                tags=tags
            )
            session.add(metric)
    
    def get_metrics(self, metric_type: str, metric_name: str, 
                   hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics for the specified time period."""
        with self.get_session() as session:
            from datetime import datetime, timedelta
            since = datetime.utcnow() - timedelta(hours=hours)
            
            metrics = session.query(SystemMetrics).filter(
                SystemMetrics.metric_type == metric_type,
                SystemMetrics.metric_name == metric_name,
                SystemMetrics.timestamp >= since
            ).order_by(SystemMetrics.timestamp.desc()).all()
            
            return [
                {
                    'value': metric.value,
                    'unit': metric.unit,
                    'tags': metric.tags,
                    'timestamp': metric.timestamp
                }
                for metric in metrics
            ]
    
    # Utility operations
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_session() as session:
            stats = {}
            
            # Count records in each table
            stats['papers'] = session.query(ResearchPaper).count()
            stats['videos'] = session.query(GeneratedVideo).count()
            stats['audio_assets'] = session.query(AudioAsset).count()
            stats['visual_assets'] = session.query(VisualAsset).count()
            stats['jobs'] = session.query(GenerationJob).count()
            
            # Get status distributions
            video_statuses = session.query(
                GeneratedVideo.status,
                session.query(GeneratedVideo).filter(
                    GeneratedVideo.status == GeneratedVideo.status
                ).count().label('count')
            ).group_by(GeneratedVideo.status).all()
            
            stats['video_statuses'] = {status: count for status, count in video_statuses}
            
            return stats
    
    def cleanup_old_metrics(self, days: int = 30):
        """Clean up old metrics data."""
        with self.get_session() as session:
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            deleted = session.query(SystemMetrics).filter(
                SystemMetrics.timestamp < cutoff
            ).delete()
            
            logger.info(f"Cleaned up {deleted} old metric records")
            return deleted


# Global database manager instance (initialized on demand)
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database():
    """Initialize database with tables and basic setup."""
    try:
        db_manager = get_db_manager()
        db_manager.create_database_if_not_exists()
        db_manager.create_tables()
        
        # Test connection
        if db_manager.test_connection():
            logger.info("Database initialized successfully")
            return True
        else:
            logger.error("Database initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False