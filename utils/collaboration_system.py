"""
Real-Time Collaboration System

This module provides comprehensive real-time collaboration features including:
- Multi-user editing and review system
- Comment and annotation system for generated content
- Approval workflows for content publication
- Real-time preview and editing capabilities
- WebSocket-based real-time communication

Optimized for 16GB RAM systems with efficient memory management.
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pathlib import Path

# WebSocket and real-time communication
try:
    import websockets
    from fastapi import WebSocket, WebSocketDisconnect
    import redis
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logging.warning("WebSocket libraries not available. Install websockets, fastapi, and redis.")

# Database integration
try:
    from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logging.warning("Database libraries not available. Install sqlalchemy and psycopg2.")

class CollaborationEventType(Enum):
    """Types of collaboration events."""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    CONTENT_EDITED = "content_edited"
    COMMENT_ADDED = "comment_added"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    CURSOR_MOVED = "cursor_moved"
    SELECTION_CHANGED = "selection_changed"

class UserRole(Enum):
    """User roles in collaboration."""
    VIEWER = "viewer"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    ADMIN = "admin"

class ApprovalStatus(Enum):
    """Approval workflow statuses."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"

@dataclass
class CollaborationUser:
    """User in collaboration session."""
    user_id: str
    username: str
    role: UserRole
    avatar_url: Optional[str] = None
    last_seen: Optional[datetime] = None
    cursor_position: Optional[Dict] = None
    selection: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['role'] = self.role.value
        data['last_seen'] = self.last_seen.isoformat() if self.last_seen else None
        return data

@dataclass
class Comment:
    """Comment on content."""
    comment_id: str
    user_id: str
    username: str
    content: str
    position: Dict  # Position in document/video
    timestamp: datetime
    resolved: bool = False
    replies: List['Comment'] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['replies'] = [reply.to_dict() for reply in self.replies]
        return data

@dataclass
class CollaborationEvent:
    """Real-time collaboration event."""
    event_id: str
    event_type: CollaborationEventType
    user_id: str
    session_id: str
    data: Dict
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }

class CollaborationSession:
    """
    Manages a real-time collaboration session for content editing and review.
    """
    
    def __init__(self, session_id: str, content_id: str, content_type: str):
        self.session_id = session_id
        self.content_id = content_id
        self.content_type = content_type  # 'video', 'audio', 'visual', 'script'
        
        self.users: Dict[str, CollaborationUser] = {}
        self.comments: Dict[str, Comment] = {}
        self.websockets: Dict[str, WebSocket] = {}
        
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Content state
        self.content_version = 1
        self.content_data = {}
        self.approval_status = ApprovalStatus.DRAFT
        
        # Event history (keep last 1000 events)
        self.event_history: List[CollaborationEvent] = []
        
        self.logger = logging.getLogger(f"collaboration.{session_id}")
    
    async def add_user(self, user: CollaborationUser, websocket: WebSocket = None) -> bool:
        """Add user to collaboration session."""
        try:
            self.users[user.user_id] = user
            if websocket:
                self.websockets[user.user_id] = websocket
            
            # Broadcast user joined event
            event = CollaborationEvent(
                event_id=str(uuid.uuid4()),
                event_type=CollaborationEventType.USER_JOINED,
                user_id=user.user_id,
                session_id=self.session_id,
                data={'user': user.to_dict()},
                timestamp=datetime.now()
            )
            
            await self._broadcast_event(event, exclude_user=user.user_id)
            self._add_event_to_history(event)
            
            self.last_activity = datetime.now()
            
            self.logger.info(f"User {user.username} joined session {self.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding user to session: {e}")
            return False
    
    async def remove_user(self, user_id: str) -> bool:
        """Remove user from collaboration session."""
        try:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            
            # Remove user and websocket
            del self.users[user_id]
            if user_id in self.websockets:
                del self.websockets[user_id]
            
            # Broadcast user left event
            event = CollaborationEvent(
                event_id=str(uuid.uuid4()),
                event_type=CollaborationEventType.USER_LEFT,
                user_id=user_id,
                session_id=self.session_id,
                data={'username': user.username},
                timestamp=datetime.now()
            )
            
            await self._broadcast_event(event)
            self._add_event_to_history(event)
            
            self.last_activity = datetime.now()
            
            self.logger.info(f"User {user.username} left session {self.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing user from session: {e}")
            return False
    
    async def add_comment(self, user_id: str, content: str, position: Dict, 
                         parent_comment_id: str = None) -> Optional[Comment]:
        """Add comment to content."""
        try:
            if user_id not in self.users:
                return None
            
            user = self.users[user_id]
            comment_id = str(uuid.uuid4())
            
            comment = Comment(
                comment_id=comment_id,
                user_id=user_id,
                username=user.username,
                content=content,
                position=position,
                timestamp=datetime.now()
            )
            
            # Handle reply to existing comment
            if parent_comment_id and parent_comment_id in self.comments:
                self.comments[parent_comment_id].replies.append(comment)
            else:
                self.comments[comment_id] = comment
            
            # Broadcast comment added event
            event = CollaborationEvent(
                event_id=str(uuid.uuid4()),
                event_type=CollaborationEventType.COMMENT_ADDED,
                user_id=user_id,
                session_id=self.session_id,
                data={
                    'comment': comment.to_dict(),
                    'parent_comment_id': parent_comment_id
                },
                timestamp=datetime.now()
            )
            
            await self._broadcast_event(event)
            self._add_event_to_history(event)
            
            self.last_activity = datetime.now()
            
            return comment
            
        except Exception as e:
            self.logger.error(f"Error adding comment: {e}")
            return None
    
    async def update_content(self, user_id: str, content_data: Dict, 
                           change_description: str = "") -> bool:
        """Update content with change tracking."""
        try:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            
            # Check permissions
            if user.role not in [UserRole.EDITOR, UserRole.ADMIN]:
                return False
            
            # Update content
            old_version = self.content_version
            self.content_data = content_data
            self.content_version += 1
            
            # Broadcast content edited event
            event = CollaborationEvent(
                event_id=str(uuid.uuid4()),
                event_type=CollaborationEventType.CONTENT_EDITED,
                user_id=user_id,
                session_id=self.session_id,
                data={
                    'old_version': old_version,
                    'new_version': self.content_version,
                    'change_description': change_description,
                    'content_data': content_data
                },
                timestamp=datetime.now()
            )
            
            await self._broadcast_event(event, exclude_user=user_id)
            self._add_event_to_history(event)
            
            self.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating content: {e}")
            return False
    
    async def request_approval(self, user_id: str, reviewers: List[str] = None) -> bool:
        """Request approval for content."""
        try:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            
            # Check permissions
            if user.role not in [UserRole.EDITOR, UserRole.ADMIN]:
                return False
            
            self.approval_status = ApprovalStatus.PENDING_REVIEW
            
            # Broadcast approval request event
            event = CollaborationEvent(
                event_id=str(uuid.uuid4()),
                event_type=CollaborationEventType.APPROVAL_REQUESTED,
                user_id=user_id,
                session_id=self.session_id,
                data={
                    'reviewers': reviewers or [],
                    'content_version': self.content_version
                },
                timestamp=datetime.now()
            )
            
            await self._broadcast_event(event)
            self._add_event_to_history(event)
            
            self.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error requesting approval: {e}")
            return False
    
    async def approve_content(self, user_id: str, approved: bool, 
                            feedback: str = "") -> bool:
        """Approve or reject content."""
        try:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            
            # Check permissions
            if user.role not in [UserRole.REVIEWER, UserRole.ADMIN]:
                return False
            
            if self.approval_status != ApprovalStatus.PENDING_REVIEW:
                return False
            
            # Update approval status
            self.approval_status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
            
            # Broadcast approval event
            event_type = CollaborationEventType.APPROVAL_GRANTED if approved else CollaborationEventType.APPROVAL_REJECTED
            event = CollaborationEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                user_id=user_id,
                session_id=self.session_id,
                data={
                    'approved': approved,
                    'feedback': feedback,
                    'content_version': self.content_version
                },
                timestamp=datetime.now()
            )
            
            await self._broadcast_event(event)
            self._add_event_to_history(event)
            
            self.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing approval: {e}")
            return False
    
    async def update_cursor_position(self, user_id: str, position: Dict) -> bool:
        """Update user's cursor position."""
        try:
            if user_id not in self.users:
                return False
            
            self.users[user_id].cursor_position = position
            self.users[user_id].last_seen = datetime.now()
            
            # Broadcast cursor movement (throttled)
            event = CollaborationEvent(
                event_id=str(uuid.uuid4()),
                event_type=CollaborationEventType.CURSOR_MOVED,
                user_id=user_id,
                session_id=self.session_id,
                data={'position': position},
                timestamp=datetime.now()
            )
            
            await self._broadcast_event(event, exclude_user=user_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating cursor position: {e}")
            return False
    
    async def _broadcast_event(self, event: CollaborationEvent, exclude_user: str = None):
        """Broadcast event to all connected users."""
        if not WEBSOCKET_AVAILABLE:
            return
        
        message = json.dumps(event.to_dict())
        
        # Send to all connected websockets
        disconnected_users = []
        
        for user_id, websocket in self.websockets.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.remove_user(user_id)
    
    def _add_event_to_history(self, event: CollaborationEvent):
        """Add event to history with size limit."""
        self.event_history.append(event)
        
        # Keep only last 1000 events to manage memory
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-1000:]
    
    def get_session_state(self) -> Dict:
        """Get current session state."""
        return {
            'session_id': self.session_id,
            'content_id': self.content_id,
            'content_type': self.content_type,
            'users': [user.to_dict() for user in self.users.values()],
            'comments': [comment.to_dict() for comment in self.comments.values()],
            'content_version': self.content_version,
            'approval_status': self.approval_status.value,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'active_users': len(self.users)
        }

class CollaborationManager:
    """
    Manages multiple collaboration sessions and provides coordination services.
    """
    
    def __init__(self, redis_config: Dict = None):
        self.sessions: Dict[str, CollaborationSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        
        # Redis for distributed collaboration (optional)
        self.redis_client = None
        if redis_config and WEBSOCKET_AVAILABLE:
            try:
                import redis
                self.redis_client = redis.Redis(**redis_config)
            except Exception as e:
                logging.warning(f"Could not connect to Redis: {e}")
        
        self.logger = logging.getLogger(__name__)
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task for session cleanup."""
        async def cleanup_inactive_sessions():
            while True:
                try:
                    await asyncio.sleep(300)  # Check every 5 minutes
                    await self._cleanup_inactive_sessions()
                except Exception as e:
                    self.logger.error(f"Error in cleanup task: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_inactive_sessions())
    
    async def create_session(self, content_id: str, content_type: str, 
                           creator_user: CollaborationUser) -> str:
        """Create new collaboration session."""
        session_id = str(uuid.uuid4())
        
        session = CollaborationSession(session_id, content_id, content_type)
        await session.add_user(creator_user)
        
        self.sessions[session_id] = session
        
        # Track user sessions
        if creator_user.user_id not in self.user_sessions:
            self.user_sessions[creator_user.user_id] = set()
        self.user_sessions[creator_user.user_id].add(session_id)
        
        self.logger.info(f"Created collaboration session {session_id} for content {content_id}")
        
        return session_id
    
    async def join_session(self, session_id: str, user: CollaborationUser, 
                          websocket: WebSocket = None) -> bool:
        """Join existing collaboration session."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        success = await session.add_user(user, websocket)
        
        if success:
            # Track user sessions
            if user.user_id not in self.user_sessions:
                self.user_sessions[user.user_id] = set()
            self.user_sessions[user.user_id].add(session_id)
        
        return success
    
    async def leave_session(self, session_id: str, user_id: str) -> bool:
        """Leave collaboration session."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        success = await session.remove_user(user_id)
        
        if success and user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            
            # Clean up empty user session tracking
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        return success
    
    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get collaboration session by ID."""
        return self.sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all sessions for a user."""
        return list(self.user_sessions.get(user_id, set()))
    
    async def _cleanup_inactive_sessions(self):
        """Clean up inactive sessions."""
        current_time = datetime.now()
        inactive_threshold = timedelta(hours=24)  # 24 hours of inactivity
        
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > inactive_threshold:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            session = self.sessions[session_id]
            
            # Remove all users
            user_ids = list(session.users.keys())
            for user_id in user_ids:
                await session.remove_user(user_id)
            
            # Remove session
            del self.sessions[session_id]
            
            self.logger.info(f"Cleaned up inactive session {session_id}")
    
    def get_active_sessions(self) -> List[Dict]:
        """Get list of all active sessions."""
        return [session.get_session_state() for session in self.sessions.values()]
    
    async def broadcast_to_all_sessions(self, event_data: Dict):
        """Broadcast event to all active sessions."""
        for session in self.sessions.values():
            event = CollaborationEvent(
                event_id=str(uuid.uuid4()),
                event_type=CollaborationEventType.USER_JOINED,  # Generic event type
                user_id="system",
                session_id=session.session_id,
                data=event_data,
                timestamp=datetime.now()
            )
            
            await session._broadcast_event(event)

# WebSocket endpoint handler
class CollaborationWebSocketHandler:
    """
    Handles WebSocket connections for real-time collaboration.
    """
    
    def __init__(self, collaboration_manager: CollaborationManager):
        self.manager = collaboration_manager
        self.logger = logging.getLogger(__name__)
    
    async def handle_websocket(self, websocket: WebSocket, session_id: str, user_data: Dict):
        """Handle WebSocket connection for collaboration."""
        if not WEBSOCKET_AVAILABLE:
            await websocket.close(code=1000, reason="WebSocket not available")
            return
        
        await websocket.accept()
        
        # Create user object
        user = CollaborationUser(
            user_id=user_data['user_id'],
            username=user_data['username'],
            role=UserRole(user_data.get('role', 'editor')),
            avatar_url=user_data.get('avatar_url')
        )
        
        # Join session
        success = await self.manager.join_session(session_id, user, websocket)
        
        if not success:
            await websocket.close(code=1000, reason="Could not join session")
            return
        
        try:
            # Send initial session state
            session = self.manager.get_session(session_id)
            if session:
                initial_state = {
                    'type': 'session_state',
                    'data': session.get_session_state()
                }
                await websocket.send_text(json.dumps(initial_state))
            
            # Handle incoming messages
            async for message in websocket.iter_text():
                await self._handle_message(session_id, user.user_id, message)
                
        except WebSocketDisconnect:
            self.logger.info(f"User {user.username} disconnected from session {session_id}")
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up
            await self.manager.leave_session(session_id, user.user_id)
    
    async def _handle_message(self, session_id: str, user_id: str, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            session = self.manager.get_session(session_id)
            if not session:
                return
            
            if message_type == 'add_comment':
                await session.add_comment(
                    user_id=user_id,
                    content=data['content'],
                    position=data['position'],
                    parent_comment_id=data.get('parent_comment_id')
                )
            
            elif message_type == 'update_content':
                await session.update_content(
                    user_id=user_id,
                    content_data=data['content_data'],
                    change_description=data.get('change_description', '')
                )
            
            elif message_type == 'cursor_move':
                await session.update_cursor_position(
                    user_id=user_id,
                    position=data['position']
                )
            
            elif message_type == 'request_approval':
                await session.request_approval(
                    user_id=user_id,
                    reviewers=data.get('reviewers', [])
                )
            
            elif message_type == 'approve_content':
                await session.approve_content(
                    user_id=user_id,
                    approved=data['approved'],
                    feedback=data.get('feedback', '')
                )
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")

# Integration with video generation system
async def create_collaboration_session_for_video(video_id: str, creator_user_id: str, 
                                               creator_username: str) -> str:
    """
    Convenience function to create collaboration session for video editing.
    
    Args:
        video_id: ID of the video being edited
        creator_user_id: ID of the user creating the session
        creator_username: Username of the creator
        
    Returns:
        Session ID for the collaboration session
    """
    manager = CollaborationManager()
    
    creator = CollaborationUser(
        user_id=creator_user_id,
        username=creator_username,
        role=UserRole.ADMIN
    )
    
    session_id = await manager.create_session(video_id, "video", creator)
    return session_id

if __name__ == "__main__":
    # Example usage
    async def main():
        print("Real-time collaboration system initialized successfully")
        print("Available features:")
        print(f"- WebSocket support: {WEBSOCKET_AVAILABLE}")
        print(f"- Database integration: {DATABASE_AVAILABLE}")
        
        # Example session creation
        manager = CollaborationManager()
        
        user = CollaborationUser(
            user_id="user123",
            username="testuser",
            role=UserRole.EDITOR
        )
        
        session_id = await manager.create_session("content123", "video", user)
        print(f"Created collaboration session: {session_id}")
        
        # Get session state
        session = manager.get_session(session_id)
        if session:
            state = session.get_session_state()
            print(f"Session has {state['active_users']} active users")
    
    asyncio.run(main())