"""
Database schema design for production video generation system.
Implements industry-standard PostgreSQL schema for research papers and generated content.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.types import TypeDecorator
from datetime import datetime
import uuid
import json as json_module


# Custom type for handling arrays in different databases
class ArrayType(TypeDecorator):
    """Custom array type that works with both PostgreSQL and SQLite."""
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(JSON())
    
    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        else:
            return json_module.dumps(value) if value is not None else None
    
    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        else:
            return json_module.loads(value) if value is not None else None


# Custom UUID type for SQLite compatibility
class UUIDType(TypeDecorator):
    """Custom UUID type that works with both PostgreSQL and SQLite."""
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return uuid.UUID(value)

Base = declarative_base()


class ResearchPaper(Base):
    """Research paper metadata and content storage."""
    __tablename__ = 'research_papers'
    
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    authors = Column(ArrayType(), nullable=False)
    doi = Column(String(100), unique=True, index=True)
    abstract = Column(Text)
    keywords = Column(ArrayType(), index=True)
    publication_date = Column(DateTime)
    journal = Column(String(200))
    arxiv_id = Column(String(50), unique=True, index=True)
    
    # File paths and organization
    file_path = Column(String(500), nullable=False)
    folder_name = Column(String(200), nullable=False, index=True)
    
    # Content analysis
    content_hash = Column(String(64), unique=True, index=True)
    page_count = Column(Integer)
    word_count = Column(Integer)
    
    # Processing status
    processing_status = Column(String(50), default='pending', index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    videos = relationship("GeneratedVideo", back_populates="paper", cascade="all, delete-orphan")
    audio_assets = relationship("AudioAsset", back_populates="paper", cascade="all, delete-orphan")
    visual_assets = relationship("VisualAsset", back_populates="paper", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_paper_search', 'title', 'authors', 'keywords'),
        Index('idx_paper_date_status', 'publication_date', 'processing_status'),
        CheckConstraint('page_count > 0', name='check_positive_pages'),
        CheckConstraint('word_count > 0', name='check_positive_words'),
    )


class GeneratedVideo(Base):
    """Generated video content and metadata."""
    __tablename__ = 'generated_videos'
    
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUIDType(), ForeignKey('research_papers.id'), nullable=False)
    
    # Video metadata
    title = Column(String(200), nullable=False)
    description = Column(Text)
    duration_seconds = Column(Float, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    
    # Technical specifications
    resolution = Column(String(20), nullable=False)  # e.g., "1920x1080"
    fps = Column(Integer, nullable=False)
    codec = Column(String(50), nullable=False)
    bitrate_kbps = Column(Integer, nullable=False)
    
    # File paths
    video_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    
    # Generation parameters
    quality_preset = Column(String(50), nullable=False)
    ai_models_used = Column(JSON)  # Store model names and versions
    generation_parameters = Column(JSON)  # Store all generation settings
    
    # Status and versioning
    version = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default='generating', index=True)
    is_published = Column(Boolean, default=False, index=True)
    
    # Timestamps
    generation_started_at = Column(DateTime, default=datetime.utcnow)
    generation_completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paper = relationship("ResearchPaper", back_populates="videos")
    scenes = relationship("VideoScene", back_populates="video", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_video_paper_status', 'paper_id', 'status'),
        Index('idx_video_published', 'is_published', 'created_at'),
        CheckConstraint('duration_seconds > 0', name='check_positive_duration'),
        CheckConstraint('file_size_bytes > 0', name='check_positive_size'),
        CheckConstraint('fps > 0', name='check_positive_fps'),
        CheckConstraint('bitrate_kbps > 0', name='check_positive_bitrate'),
    )


class VideoScene(Base):
    """Individual scenes within generated videos."""
    __tablename__ = 'video_scenes'
    
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUIDType(), ForeignKey('generated_videos.id'), nullable=False)
    
    # Scene metadata
    scene_number = Column(Integer, nullable=False)
    title = Column(String(200))
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float, nullable=False)
    
    # Content information
    scene_type = Column(String(50), nullable=False)  # intro, content, conclusion, etc.
    content_summary = Column(Text)
    
    # Animation and visual details
    animation_type = Column(String(50))  # manim, motion_canvas, remotion, etc.
    visual_style = Column(String(50))
    generated_code_path = Column(String(500))
    
    # Relationships
    video = relationship("GeneratedVideo", back_populates="scenes")
    
    __table_args__ = (
        Index('idx_scene_video_number', 'video_id', 'scene_number'),
        UniqueConstraint('video_id', 'scene_number', name='uq_video_scene_number'),
        CheckConstraint('start_time_seconds >= 0', name='check_non_negative_start'),
        CheckConstraint('end_time_seconds > start_time_seconds', name='check_valid_duration'),
    )


class AudioAsset(Base):
    """Audio assets including narration, music, and effects."""
    __tablename__ = 'audio_assets'
    
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUIDType(), ForeignKey('research_papers.id'), nullable=False)
    
    # Audio metadata
    asset_type = Column(String(50), nullable=False, index=True)  # narration, music, effects
    title = Column(String(200))
    duration_seconds = Column(Float, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    
    # Technical specifications
    sample_rate = Column(Integer, nullable=False)
    channels = Column(Integer, nullable=False)
    bitrate_kbps = Column(Integer, nullable=False)
    format = Column(String(20), nullable=False)
    
    # File path
    file_path = Column(String(500), nullable=False)
    
    # Generation details
    tts_model = Column(String(100))  # For narration assets
    voice_style = Column(String(50))  # For narration assets
    music_model = Column(String(100))  # For music assets
    generation_parameters = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paper = relationship("ResearchPaper", back_populates="audio_assets")
    
    __table_args__ = (
        Index('idx_audio_paper_type', 'paper_id', 'asset_type'),
        CheckConstraint('duration_seconds > 0', name='check_positive_audio_duration'),
        CheckConstraint('file_size_bytes > 0', name='check_positive_audio_size'),
        CheckConstraint('sample_rate > 0', name='check_positive_sample_rate'),
        CheckConstraint('channels > 0', name='check_positive_channels'),
        CheckConstraint('bitrate_kbps > 0', name='check_positive_audio_bitrate'),
    )


class VisualAsset(Base):
    """Visual assets including animations, diagrams, and 3D models."""
    __tablename__ = 'visual_assets'
    
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUIDType(), ForeignKey('research_papers.id'), nullable=False)
    
    # Visual metadata
    asset_type = Column(String(50), nullable=False, index=True)  # animation, diagram, 3d_model, chart
    title = Column(String(200))
    description = Column(Text)
    
    # Technical specifications
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    format = Column(String(20), nullable=False)  # mp4, png, svg, blend, etc.
    file_size_bytes = Column(Integer, nullable=False)
    
    # File paths
    file_path = Column(String(500), nullable=False)
    source_code_path = Column(String(500))  # For generated animations
    
    # Generation details
    generation_framework = Column(String(50))  # manim, motion_canvas, remotion, blender
    ai_model_used = Column(String(100))
    generation_parameters = Column(JSON)
    
    # Visual style and branding
    color_palette = Column(JSON)
    visual_theme = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paper = relationship("ResearchPaper", back_populates="visual_assets")
    
    __table_args__ = (
        Index('idx_visual_paper_type', 'paper_id', 'asset_type'),
        Index('idx_visual_framework', 'generation_framework'),
        CheckConstraint('width > 0', name='check_positive_width'),
        CheckConstraint('height > 0', name='check_positive_height'),
        CheckConstraint('file_size_bytes > 0', name='check_positive_visual_size'),
    )


class ContentVersion(Base):
    """Version tracking for all generated content."""
    __tablename__ = 'content_versions'
    
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    
    # Content reference
    content_type = Column(String(50), nullable=False, index=True)  # video, audio, visual
    content_id = Column(UUIDType(), nullable=False, index=True)
    
    # Version information
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(100))
    change_description = Column(Text)
    
    # Generation parameters for this version
    generation_parameters = Column(JSON, nullable=False)
    ai_models_used = Column(JSON)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(100))  # User or system identifier
    
    __table_args__ = (
        Index('idx_version_content', 'content_type', 'content_id', 'version_number'),
        UniqueConstraint('content_type', 'content_id', 'version_number', 
                        name='uq_content_version'),
        CheckConstraint('version_number > 0', name='check_positive_version'),
        CheckConstraint('file_size_bytes > 0', name='check_positive_version_size'),
    )


class GenerationJob(Base):
    """Track generation jobs and their status."""
    __tablename__ = 'generation_jobs'
    
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUIDType(), ForeignKey('research_papers.id'), nullable=False)
    
    # Job metadata
    job_type = Column(String(50), nullable=False, index=True)  # video, audio, visual
    job_name = Column(String(200), nullable=False)
    priority = Column(Integer, default=5, index=True)  # 1-10, higher is more priority
    
    # Job parameters
    generation_parameters = Column(JSON, nullable=False)
    ai_models_requested = Column(JSON)
    
    # Status tracking
    status = Column(String(50), default='queued', nullable=False, index=True)
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(200))
    
    # Resource usage
    estimated_duration_minutes = Column(Integer)
    actual_duration_minutes = Column(Integer)
    memory_usage_mb = Column(Integer)
    gpu_usage_percentage = Column(Float)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Results
    output_content_ids = Column(JSON)  # IDs of generated content
    
    __table_args__ = (
        Index('idx_job_status_priority', 'status', 'priority'),
        Index('idx_job_paper_type', 'paper_id', 'job_type'),
        CheckConstraint('priority >= 1 AND priority <= 10', name='check_valid_priority'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', 
                       name='check_valid_progress'),
        CheckConstraint('retry_count >= 0', name='check_non_negative_retries'),
        CheckConstraint('max_retries >= 0', name='check_non_negative_max_retries'),
    )


class SystemMetrics(Base):
    """System performance and usage metrics."""
    __tablename__ = 'system_metrics'
    
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    
    # Metric metadata
    metric_type = Column(String(50), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    
    # Metric values
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    tags = Column(JSON)  # Additional metadata
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_metrics_type_name_time', 'metric_type', 'metric_name', 'timestamp'),
    )


# Database utility functions
def create_all_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)


def get_table_names():
    """Get list of all table names."""
    return [table.name for table in Base.metadata.tables.values()]


def get_indexes():
    """Get list of all indexes for optimization."""
    indexes = []
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            indexes.append({
                'table': table.name,
                'name': index.name,
                'columns': [col.name for col in index.columns]
            })
    return indexes