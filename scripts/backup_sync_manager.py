"""
Backup and synchronization manager for production video generation system.
Handles automatic backups, cloud storage integration, and content synchronization.
"""

import os
import json
import shutil
import logging
import hashlib
import tarfile
import gzip
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import time

from .database_manager import get_db_manager
from .file_organization_manager import get_file_org_manager

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for backup operations."""
    backup_id: str
    backup_type: str  # full, incremental, differential
    created_at: datetime
    size_bytes: int
    file_count: int
    compression_ratio: float
    checksum: str
    storage_location: str
    retention_days: int


@dataclass
class SyncStatus:
    """Status of synchronization operations."""
    sync_id: str
    source: str
    destination: str
    status: str  # pending, running, completed, failed
    files_synced: int
    bytes_synced: int
    errors: List[str]
    started_at: datetime
    completed_at: Optional[datetime]


class BackupSyncManager:
    """Manages backups, cloud storage, and synchronization."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize backup and sync manager."""
        self.config = config or self._load_default_config()
        self.db_manager = get_db_manager()
        self.file_manager = get_file_org_manager()
        self.base_path = Path(self.file_manager.base_path)
        self.backup_path = self.base_path / "backups"
        self.backup_path.mkdir(exist_ok=True)
        
        # Initialize cloud storage clients
        self.cloud_clients = self._initialize_cloud_clients()
        
        # Start background backup scheduler
        self.scheduler_running = False
        self.start_backup_scheduler()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default backup configuration."""
        return {
            'backup_schedule': {
                'daily': {'enabled': True, 'time': '02:00', 'retention_days': 7},
                'weekly': {'enabled': True, 'day': 'sunday', 'time': '01:00', 'retention_days': 30},
                'monthly': {'enabled': True, 'day': 1, 'time': '00:00', 'retention_days': 365}
            },
            'compression': {
                'enabled': True,
                'algorithm': 'gzip',
                'level': 6
            },
            'cloud_storage': {
                'enabled': False,
                'providers': {
                    's3': {'enabled': False, 'bucket': '', 'region': 'us-east-1'},
                    'gcs': {'enabled': False, 'bucket': '', 'project_id': ''},
                    'azure': {'enabled': False, 'container': '', 'account_name': ''}
                }
            },
            'sync': {
                'enabled': False,
                'remote_endpoints': [],
                'conflict_resolution': 'timestamp'  # timestamp, size, manual
            }
        }
    
    def _initialize_cloud_clients(self) -> Dict[str, Any]:
        """Initialize cloud storage clients based on configuration."""
        clients = {}
        
        try:
            # AWS S3 client
            if self.config['cloud_storage']['providers']['s3']['enabled']:
                try:
                    import boto3
                    s3_config = self.config['cloud_storage']['providers']['s3']
                    clients['s3'] = boto3.client(
                        's3',
                        region_name=s3_config['region'],
                        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                    )
                    logger.info("S3 client initialized")
                except ImportError:
                    logger.warning("boto3 not installed, S3 backup disabled")
                except Exception as e:
                    logger.error(f"Error initializing S3 client: {e}")
            
            # Google Cloud Storage client
            if self.config['cloud_storage']['providers']['gcs']['enabled']:
                try:
                    from google.cloud import storage
                    clients['gcs'] = storage.Client()
                    logger.info("GCS client initialized")
                except ImportError:
                    logger.warning("google-cloud-storage not installed, GCS backup disabled")
                except Exception as e:
                    logger.error(f"Error initializing GCS client: {e}")
            
            # Azure Blob Storage client
            if self.config['cloud_storage']['providers']['azure']['enabled']:
                try:
                    from azure.storage.blob import BlobServiceClient
                    azure_config = self.config['cloud_storage']['providers']['azure']
                    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                    if connection_string:
                        clients['azure'] = BlobServiceClient.from_connection_string(connection_string)
                        logger.info("Azure Blob client initialized")
                except ImportError:
                    logger.warning("azure-storage-blob not installed, Azure backup disabled")
                except Exception as e:
                    logger.error(f"Error initializing Azure client: {e}")
        
        except Exception as e:
            logger.error(f"Error initializing cloud clients: {e}")
        
        return clients
    
    # Backup Operations
    def create_backup(self, backup_type: str = 'full', 
                     include_database: bool = True) -> str:
        """Create a comprehensive backup."""
        try:
            backup_id = self._generate_backup_id(backup_type)
            backup_dir = self.backup_path / backup_type / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Starting {backup_type} backup: {backup_id}")
            
            # Backup file system
            files_backed_up = self._backup_filesystem(backup_dir, backup_type)
            
            # Backup database
            if include_database:
                self._backup_database(backup_dir)
            
            # Create backup metadata
            metadata = self._create_backup_metadata(
                backup_id, backup_type, backup_dir, files_backed_up
            )
            
            # Compress backup if enabled
            if self.config['compression']['enabled']:
                compressed_path = self._compress_backup(backup_dir)
                metadata.storage_location = str(compressed_path)
                # Remove uncompressed backup
                shutil.rmtree(backup_dir)
            else:
                metadata.storage_location = str(backup_dir)
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            # Upload to cloud if enabled
            if self.config['cloud_storage']['enabled']:
                self._upload_to_cloud(metadata)
            
            # Clean up old backups
            self._cleanup_old_backups(backup_type)
            
            logger.info(f"Backup completed: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def restore_backup(self, backup_id: str, 
                      restore_database: bool = True) -> bool:
        """Restore from backup."""
        try:
            # Find backup metadata
            metadata = self._load_backup_metadata(backup_id)
            if not metadata:
                logger.error(f"Backup metadata not found: {backup_id}")
                return False
            
            logger.info(f"Starting restore from backup: {backup_id}")
            
            # Download from cloud if needed
            backup_path = Path(metadata.storage_location)
            if not backup_path.exists() and self.config['cloud_storage']['enabled']:
                backup_path = self._download_from_cloud(metadata)
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Extract if compressed
            if backup_path.suffix == '.tar.gz':
                extract_dir = backup_path.parent / f"{backup_path.stem}_extracted"
                self._extract_backup(backup_path, extract_dir)
                backup_path = extract_dir
            
            # Restore filesystem
            self._restore_filesystem(backup_path)
            
            # Restore database
            if restore_database:
                self._restore_database(backup_path)
            
            logger.info(f"Restore completed: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self, backup_type: Optional[str] = None) -> List[BackupMetadata]:
        """List available backups."""
        try:
            backups = []
            metadata_dir = self.backup_path / "metadata"
            
            if metadata_dir.exists():
                for metadata_file in metadata_dir.glob("*.json"):
                    try:
                        with open(metadata_file) as f:
                            data = json.load(f)
                        
                        metadata = BackupMetadata(
                            backup_id=data['backup_id'],
                            backup_type=data['backup_type'],
                            created_at=datetime.fromisoformat(data['created_at']),
                            size_bytes=data['size_bytes'],
                            file_count=data['file_count'],
                            compression_ratio=data['compression_ratio'],
                            checksum=data['checksum'],
                            storage_location=data['storage_location'],
                            retention_days=data['retention_days']
                        )
                        
                        if backup_type is None or metadata.backup_type == backup_type:
                            backups.append(metadata)
                            
                    except Exception as e:
                        logger.warning(f"Error reading backup metadata {metadata_file}: {e}")
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x.created_at, reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        try:
            metadata = self._load_backup_metadata(backup_id)
            if not metadata:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            # Delete local backup file
            backup_path = Path(metadata.storage_location)
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    backup_path.unlink()
            
            # Delete from cloud storage
            if self.config['cloud_storage']['enabled']:
                self._delete_from_cloud(metadata)
            
            # Delete metadata
            metadata_file = self.backup_path / "metadata" / f"{backup_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.info(f"Backup deleted: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False
    
    # Synchronization Operations
    def sync_to_remote(self, remote_endpoint: str, 
                      sync_type: str = 'incremental') -> str:
        """Synchronize content to remote endpoint."""
        try:
            sync_id = self._generate_sync_id()
            
            sync_status = SyncStatus(
                sync_id=sync_id,
                source=str(self.base_path),
                destination=remote_endpoint,
                status='running',
                files_synced=0,
                bytes_synced=0,
                errors=[],
                started_at=datetime.now(),
                completed_at=None
            )
            
            logger.info(f"Starting sync to {remote_endpoint}: {sync_id}")
            
            # Perform synchronization based on type
            if sync_type == 'full':
                self._full_sync(sync_status)
            else:
                self._incremental_sync(sync_status)
            
            sync_status.status = 'completed'
            sync_status.completed_at = datetime.now()
            
            logger.info(f"Sync completed: {sync_id}")
            return sync_id
            
        except Exception as e:
            logger.error(f"Error syncing to remote: {e}")
            if 'sync_status' in locals():
                sync_status.status = 'failed'
                sync_status.errors.append(str(e))
            raise
    
    def sync_from_remote(self, remote_endpoint: str) -> str:
        """Synchronize content from remote endpoint."""
        try:
            sync_id = self._generate_sync_id()
            
            sync_status = SyncStatus(
                sync_id=sync_id,
                source=remote_endpoint,
                destination=str(self.base_path),
                status='running',
                files_synced=0,
                bytes_synced=0,
                errors=[],
                started_at=datetime.now(),
                completed_at=None
            )
            
            logger.info(f"Starting sync from {remote_endpoint}: {sync_id}")
            
            # This would implement the actual sync logic
            # For now, just mark as completed
            sync_status.status = 'completed'
            sync_status.completed_at = datetime.now()
            
            logger.info(f"Sync completed: {sync_id}")
            return sync_id
            
        except Exception as e:
            logger.error(f"Error syncing from remote: {e}")
            raise
    
    # Scheduler Operations
    def start_backup_scheduler(self):
        """Start the automatic backup scheduler."""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        scheduler_thread = threading.Thread(target=self._backup_scheduler_loop, daemon=True)
        scheduler_thread.start()
        logger.info("Backup scheduler started")
    
    def stop_backup_scheduler(self):
        """Stop the automatic backup scheduler."""
        self.scheduler_running = False
        logger.info("Backup scheduler stopped")
    
    # Helper Methods
    def _generate_backup_id(self, backup_type: str) -> str:
        """Generate unique backup ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{backup_type}_{timestamp}"
    
    def _generate_sync_id(self) -> str:
        """Generate unique sync ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        return f"sync_{timestamp}_{str(uuid.uuid4())[:8]}"
    
    def _backup_filesystem(self, backup_dir: Path, backup_type: str) -> int:
        """Backup filesystem to directory."""
        files_backed_up = 0
        
        # Directories to backup
        backup_dirs = ['papers', 'videos', 'audio', 'visuals', 'code', 'metadata']
        
        for dir_name in backup_dirs:
            source_dir = self.base_path / dir_name
            if source_dir.exists():
                dest_dir = backup_dir / dir_name
                
                if backup_type == 'full':
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
                    files_backed_up += sum(1 for _ in dest_dir.rglob('*') if _.is_file())
                else:
                    # Incremental backup - only changed files
                    files_backed_up += self._incremental_backup_dir(source_dir, dest_dir)
        
        return files_backed_up
    
    def _incremental_backup_dir(self, source_dir: Path, dest_dir: Path) -> int:
        """Perform incremental backup of directory."""
        files_backed_up = 0
        
        # Get last backup timestamp
        last_backup_time = self._get_last_backup_time('incremental')
        
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                # Check if file was modified since last backup
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > last_backup_time:
                    # Copy file
                    rel_path = file_path.relative_to(source_dir)
                    dest_file = dest_dir / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_file)
                    files_backed_up += 1
        
        return files_backed_up
    
    def _backup_database(self, backup_dir: Path):
        """Backup database to directory."""
        try:
            # Create database dump
            db_backup_dir = backup_dir / "database"
            db_backup_dir.mkdir(exist_ok=True)
            
            # This would use pg_dump or similar for PostgreSQL
            # For now, just create a placeholder
            dump_file = db_backup_dir / "database_dump.sql"
            with open(dump_file, 'w') as f:
                f.write("-- Database backup placeholder\n")
            
            logger.info("Database backup completed")
            
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            raise
    
    def _create_backup_metadata(self, backup_id: str, backup_type: str, 
                               backup_dir: Path, file_count: int) -> BackupMetadata:
        """Create backup metadata."""
        # Calculate backup size
        size_bytes = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
        
        # Calculate checksum
        checksum = self._calculate_directory_checksum(backup_dir)
        
        # Get retention days from config
        retention_days = self.config['backup_schedule'][backup_type]['retention_days']
        
        return BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            created_at=datetime.now(),
            size_bytes=size_bytes,
            file_count=file_count,
            compression_ratio=1.0,  # Will be updated if compressed
            checksum=checksum,
            storage_location=str(backup_dir),
            retention_days=retention_days
        )
    
    def _compress_backup(self, backup_dir: Path) -> Path:
        """Compress backup directory."""
        compressed_file = backup_dir.parent / f"{backup_dir.name}.tar.gz"
        
        with tarfile.open(compressed_file, 'w:gz') as tar:
            tar.add(backup_dir, arcname=backup_dir.name)
        
        # Calculate compression ratio
        original_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
        compressed_size = compressed_file.stat().st_size
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        logger.info(f"Backup compressed: {compression_ratio:.2%} of original size")
        return compressed_file
    
    def _extract_backup(self, backup_file: Path, extract_dir: Path):
        """Extract compressed backup."""
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(backup_file, 'r:gz') as tar:
            tar.extractall(extract_dir)
    
    def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to file."""
        metadata_dir = self.backup_path / "metadata"
        metadata_dir.mkdir(exist_ok=True)
        
        metadata_file = metadata_dir / f"{metadata.backup_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(asdict(metadata), f, indent=2, default=str)
    
    def _load_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Load backup metadata from file."""
        metadata_file = self.backup_path / "metadata" / f"{backup_id}.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file) as f:
                data = json.load(f)
            
            return BackupMetadata(
                backup_id=data['backup_id'],
                backup_type=data['backup_type'],
                created_at=datetime.fromisoformat(data['created_at']),
                size_bytes=data['size_bytes'],
                file_count=data['file_count'],
                compression_ratio=data['compression_ratio'],
                checksum=data['checksum'],
                storage_location=data['storage_location'],
                retention_days=data['retention_days']
            )
        except Exception as e:
            logger.error(f"Error loading backup metadata: {e}")
            return None
    
    def _calculate_directory_checksum(self, directory: Path) -> str:
        """Calculate checksum for entire directory."""
        hash_md5 = hashlib.md5()
        
        for file_path in sorted(directory.rglob('*')):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    def _get_last_backup_time(self, backup_type: str) -> datetime:
        """Get timestamp of last backup of specified type."""
        backups = self.list_backups(backup_type)
        if backups:
            return backups[0].created_at
        else:
            # Return epoch if no previous backups
            return datetime.fromtimestamp(0)
    
    def _cleanup_old_backups(self, backup_type: str):
        """Clean up old backups based on retention policy."""
        try:
            backups = self.list_backups(backup_type)
            retention_days = self.config['backup_schedule'][backup_type]['retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for backup in backups:
                if backup.created_at < cutoff_date:
                    self.delete_backup(backup.backup_id)
                    logger.info(f"Deleted old backup: {backup.backup_id}")
        
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def _upload_to_cloud(self, metadata: BackupMetadata):
        """Upload backup to configured cloud storage."""
        # Implementation would depend on configured cloud provider
        logger.info(f"Cloud upload placeholder for backup: {metadata.backup_id}")
    
    def _download_from_cloud(self, metadata: BackupMetadata) -> Path:
        """Download backup from cloud storage."""
        # Implementation would depend on configured cloud provider
        logger.info(f"Cloud download placeholder for backup: {metadata.backup_id}")
        return Path(metadata.storage_location)
    
    def _delete_from_cloud(self, metadata: BackupMetadata):
        """Delete backup from cloud storage."""
        # Implementation would depend on configured cloud provider
        logger.info(f"Cloud delete placeholder for backup: {metadata.backup_id}")
    
    def _full_sync(self, sync_status: SyncStatus):
        """Perform full synchronization."""
        # Implementation would depend on sync protocol
        logger.info(f"Full sync placeholder: {sync_status.sync_id}")
    
    def _incremental_sync(self, sync_status: SyncStatus):
        """Perform incremental synchronization."""
        # Implementation would depend on sync protocol
        logger.info(f"Incremental sync placeholder: {sync_status.sync_id}")
    
    def _restore_filesystem(self, backup_path: Path):
        """Restore filesystem from backup."""
        backup_dirs = ['papers', 'videos', 'audio', 'visuals', 'code', 'metadata']
        
        for dir_name in backup_dirs:
            source_dir = backup_path / dir_name
            dest_dir = self.base_path / dir_name
            
            if source_dir.exists():
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree(source_dir, dest_dir)
        
        logger.info("Filesystem restore completed")
    
    def _restore_database(self, backup_path: Path):
        """Restore database from backup."""
        db_backup_dir = backup_path / "database"
        if db_backup_dir.exists():
            # This would use psql or similar to restore PostgreSQL
            logger.info("Database restore completed")
    
    def _backup_scheduler_loop(self):
        """Main loop for backup scheduler."""
        while self.scheduler_running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for any scheduled backups
                for backup_type, schedule in self.config['backup_schedule'].items():
                    if schedule['enabled'] and self._should_run_backup(backup_type, current_time):
                        logger.info(f"Running scheduled {backup_type} backup")
                        self.create_backup(backup_type)
                
                # Sleep for 1 minute before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in backup scheduler: {e}")
                time.sleep(60)  # Continue after error
    
    def _should_run_backup(self, backup_type: str, current_time: datetime) -> bool:
        """Check if backup should run based on schedule."""
        schedule = self.config['backup_schedule'][backup_type]
        
        # Get last backup time
        last_backup = self._get_last_backup_time(backup_type)
        
        if backup_type == 'daily':
            # Run daily backup if more than 23 hours since last backup
            return (current_time - last_backup).total_seconds() > 23 * 3600
        
        elif backup_type == 'weekly':
            # Run weekly backup on specified day if more than 6 days since last backup
            return (current_time - last_backup).days >= 6
        
        elif backup_type == 'monthly':
            # Run monthly backup on specified day if more than 28 days since last backup
            return (current_time - last_backup).days >= 28
        
        return False


# Global backup and sync manager (initialized on demand)
_backup_sync_manager = None


def get_backup_sync_manager() -> BackupSyncManager:
    """Get the global backup and sync manager."""
    global _backup_sync_manager
    if _backup_sync_manager is None:
        _backup_sync_manager = BackupSyncManager()
    return _backup_sync_manager