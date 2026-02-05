"""
Real-time Collaboration System

This module provides comprehensive collaboration features including:
- Multi-user editing and review system
- Comment and annotation system for generated content
- Real-time preview and editing capabilities
- Approval workflows for content publication
"""

import logging
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import uuid
from pathlib import Path
import hashlib
import websockets
from websockets.server import WebSocketServerProtocol
import sqlite3
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles in the collaboration system."""
    VIEWER = "viewer"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    ADMIN = "admin"
    OWNER = "owner"

class ContentType(Enum):
    """Types of content that can be collaborated on."""
    VIDEO = "video"
    AUDIO = "audio"
    VISUAL = "visual"
    SCRIPT = "script"
    PAPER = "paper"

class CommentType(Enum):
    """Types of comments."""
    GENERAL = "general"
    SUGGESTION = "suggestion"
    ISSUE = "issue"
    APPROVAL = "approval"
    REJECTION = "rejection"

class WorkflowStatus(Enum):
    """Workflow approval statuses."""
    DRAFT = "draft"
    REVIEW_REQUESTED = "review_requested"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"

@dataclass
class User:
    """Represents a user in the collaboration system."""
    user_id: str
    username: str
    email: str
    role: UserRole
    display_name: str
    avatar_url: Optional[str] = None
    is_online: bool = False
    last_seen: Optional[datetime] = None
    permissions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Comment:
    """Represents a comment or annotation."""
    comment_id: str
    content_id: str
    content_type: ContentType
    user_id: str
    comment_type: CommentType
    text: str
    timestamp: datetime
    position: Optional[Dict[str, Any]] = None  # For positioning annotations
    thread_id: Optional[str] = None  # For threaded discussions
    parent_comment_id: Optional[str] = None
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    attachments: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EditSession:
    """Represents an active editing session."""
    session_id: str
    content_id: str
    content_type: ContentType
    user_id: str
    started_at: datetime
    last_activity: datetime
    is_active: bool = True
    locked_sections: Set[str] = field(default_factory=set)
    changes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowStep:
    """Represents a step in an approval workflow."""
    step_id: str
    workflow_id: str
    step_name: str
    step_order: int
    required_role: UserRole
    required_users: List[str] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    assigned_to: Optional[str] = None
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    comments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ApprovalWorkflow:
    """Represents an approval workflow for content."""
    workflow_id: str
    content_id: str
    content_type: ContentType
    created_by: str
    created_at: datetime
    current_step: int = 0
    status: WorkflowStatus = WorkflowStatus.DRAFT
    steps: List[WorkflowStep] = field(default_factory=list)
    deadline: Optional[datetime] = None
    priority: str = "normal"  # low, normal, high, urgent
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RealTimeEvent:
    """Represents a real-time event for collaboration."""
    event_id: str
    event_type: str
    content_id: str
    user_id: str
    timestamp: datetime
    data: Dict[str, Any]
    recipients: List[str] = field(default_factory=list)  # Empty = broadcast

class CollaborationDatabase:
    """Database manager for collaboration data."""
    
    def __init__(self, db_path: str):
        """Initialize the collaboration database."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    avatar_url TEXT,
                    is_online BOOLEAN DEFAULT FALSE,
                    last_seen TIMESTAMP,
                    permissions TEXT,
                    metadata TEXT
                );
                
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    comment_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    position TEXT,
                    thread_id TEXT,
                    parent_comment_id TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_by TEXT,
                    resolved_at TIMESTAMP,
                    attachments TEXT,
                    mentions TEXT,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                );
                
                CREATE TABLE IF NOT EXISTS edit_sessions (
                    session_id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    locked_sections TEXT,
                    changes TEXT,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                );
                
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    current_step INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'draft',
                    deadline TIMESTAMP,
                    priority TEXT DEFAULT 'normal',
                    metadata TEXT,
                    FOREIGN KEY (created_by) REFERENCES users (user_id)
                );
                
                CREATE TABLE IF NOT EXISTS workflow_steps (
                    step_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    step_order INTEGER NOT NULL,
                    required_role TEXT NOT NULL,
                    required_users TEXT,
                    status TEXT DEFAULT 'draft',
                    assigned_to TEXT,
                    completed_by TEXT,
                    completed_at TIMESTAMP,
                    comments TEXT,
                    metadata TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (workflow_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_comments_content ON comments (content_id, content_type);
                CREATE INDEX IF NOT EXISTS idx_comments_user ON comments (user_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_content ON edit_sessions (content_id, content_type);
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON edit_sessions (user_id);
                CREATE INDEX IF NOT EXISTS idx_workflows_content ON workflows (content_id, content_type);
            """)
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection with async context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    async def create_user(self, user: User) -> bool:
        """Create a new user."""
        try:
            async with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (
                        user_id, username, email, role, display_name, avatar_url,
                        is_online, last_seen, permissions, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id, user.username, user.email, user.role.value,
                    user.display_name, user.avatar_url, user.is_online,
                    user.last_seen, json.dumps(list(user.permissions)),
                    json.dumps(user.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            async with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                
                if row:
                    return User(
                        user_id=row['user_id'],
                        username=row['username'],
                        email=row['email'],
                        role=UserRole(row['role']),
                        display_name=row['display_name'],
                        avatar_url=row['avatar_url'],
                        is_online=bool(row['is_online']),
                        last_seen=datetime.fromisoformat(row['last_seen']) if row['last_seen'] else None,
                        permissions=set(json.loads(row['permissions'] or '[]')),
                        metadata=json.loads(row['metadata'] or '{}')
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def create_comment(self, comment: Comment) -> bool:
        """Create a new comment."""
        try:
            async with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO comments (
                        comment_id, content_id, content_type, user_id, comment_type,
                        text, timestamp, position, thread_id, parent_comment_id,
                        resolved, resolved_by, resolved_at, attachments, mentions, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    comment.comment_id, comment.content_id, comment.content_type.value,
                    comment.user_id, comment.comment_type.value, comment.text,
                    comment.timestamp, json.dumps(comment.position),
                    comment.thread_id, comment.parent_comment_id, comment.resolved,
                    comment.resolved_by, comment.resolved_at,
                    json.dumps(comment.attachments), json.dumps(comment.mentions),
                    json.dumps(comment.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            return False
    
    async def get_comments(self, content_id: str, content_type: ContentType) -> List[Comment]:
        """Get all comments for content."""
        try:
            async with self.get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM comments 
                    WHERE content_id = ? AND content_type = ?
                    ORDER BY timestamp ASC
                """, (content_id, content_type.value)).fetchall()
                
                comments = []
                for row in rows:
                    comment = Comment(
                        comment_id=row['comment_id'],
                        content_id=row['content_id'],
                        content_type=ContentType(row['content_type']),
                        user_id=row['user_id'],
                        comment_type=CommentType(row['comment_type']),
                        text=row['text'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        position=json.loads(row['position'] or 'null'),
                        thread_id=row['thread_id'],
                        parent_comment_id=row['parent_comment_id'],
                        resolved=bool(row['resolved']),
                        resolved_by=row['resolved_by'],
                        resolved_at=datetime.fromisoformat(row['resolved_at']) if row['resolved_at'] else None,
                        attachments=json.loads(row['attachments'] or '[]'),
                        mentions=json.loads(row['mentions'] or '[]'),
                        metadata=json.loads(row['metadata'] or '{}')
                    )
                    comments.append(comment)
                
                return comments
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []

class RealTimeCollaborationServer:
    """WebSocket server for real-time collaboration."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize the collaboration server."""
        self.host = host
        self.port = port
        self.connected_clients: Dict[str, WebSocketServerProtocol] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> websocket_id
        self.content_subscribers: Dict[str, Set[str]] = {}  # content_id -> set of user_ids
        self.event_handlers: Dict[str, Callable] = {}
        
        # Register default event handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers."""
        self.event_handlers.update({
            'user_join': self._handle_user_join,
            'user_leave': self._handle_user_leave,
            'content_subscribe': self._handle_content_subscribe,
            'content_unsubscribe': self._handle_content_unsubscribe,
            'edit_start': self._handle_edit_start,
            'edit_change': self._handle_edit_change,
            'edit_end': self._handle_edit_end,
            'comment_add': self._handle_comment_add,
            'comment_resolve': self._handle_comment_resolve,
            'cursor_move': self._handle_cursor_move,
            'selection_change': self._handle_selection_change
        })
    
    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting collaboration server on {self.host}:{self.port}")
        
        async def handle_client(websocket: WebSocketServerProtocol, path: str):
            await self._handle_client_connection(websocket, path)
        
        server = await websockets.serve(handle_client, self.host, self.port)
        logger.info("Collaboration server started successfully")
        
        try:
            await server.wait_closed()
        except KeyboardInterrupt:
            logger.info("Shutting down collaboration server")
            server.close()
            await server.wait_closed()
    
    async def _handle_client_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new client connection."""
        client_id = str(uuid.uuid4())
        self.connected_clients[client_id] = websocket
        
        logger.info(f"Client {client_id} connected")
        
        try:
            async for message in websocket:
                await self._handle_message(client_id, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            await self._cleanup_client(client_id)
    
    async def _handle_message(self, client_id: str, message: str):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            event_type = data.get('type')
            
            if event_type in self.event_handlers:
                await self.event_handlers[event_type](client_id, data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
    
    async def _cleanup_client(self, client_id: str):
        """Clean up client connection."""
        # Remove from connected clients
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        
        # Find and remove user session
        user_id = None
        for uid, cid in self.user_sessions.items():
            if cid == client_id:
                user_id = uid
                break
        
        if user_id:
            del self.user_sessions[user_id]
            
            # Remove from content subscriptions
            for content_id, subscribers in self.content_subscribers.items():
                subscribers.discard(user_id)
            
            # Broadcast user offline event
            await self._broadcast_event({
                'type': 'user_offline',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _handle_user_join(self, client_id: str, data: Dict[str, Any]):
        """Handle user join event."""
        user_id = data.get('user_id')
        if user_id:
            self.user_sessions[user_id] = client_id
            
            # Send confirmation to user
            await self._send_to_client(client_id, {
                'type': 'user_joined',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
            
            # Broadcast to other users
            await self._broadcast_event({
                'type': 'user_online',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }, exclude=[user_id])
    
    async def _handle_user_leave(self, client_id: str, data: Dict[str, Any]):
        """Handle user leave event."""
        user_id = data.get('user_id')
        if user_id and user_id in self.user_sessions:
            del self.user_sessions[user_id]
            
            await self._broadcast_event({
                'type': 'user_offline',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _handle_content_subscribe(self, client_id: str, data: Dict[str, Any]):
        """Handle content subscription."""
        user_id = data.get('user_id')
        content_id = data.get('content_id')
        
        if user_id and content_id:
            if content_id not in self.content_subscribers:
                self.content_subscribers[content_id] = set()
            
            self.content_subscribers[content_id].add(user_id)
            
            # Send confirmation
            await self._send_to_client(client_id, {
                'type': 'content_subscribed',
                'content_id': content_id,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _handle_content_unsubscribe(self, client_id: str, data: Dict[str, Any]):
        """Handle content unsubscription."""
        user_id = data.get('user_id')
        content_id = data.get('content_id')
        
        if user_id and content_id and content_id in self.content_subscribers:
            self.content_subscribers[content_id].discard(user_id)
    
    async def _handle_edit_start(self, client_id: str, data: Dict[str, Any]):
        """Handle edit session start."""
        await self._broadcast_to_content_subscribers(
            data.get('content_id'),
            {
                'type': 'edit_started',
                'user_id': data.get('user_id'),
                'content_id': data.get('content_id'),
                'section': data.get('section'),
                'timestamp': datetime.now().isoformat()
            },
            exclude=[data.get('user_id')]
        )
    
    async def _handle_edit_change(self, client_id: str, data: Dict[str, Any]):
        """Handle edit change event."""
        await self._broadcast_to_content_subscribers(
            data.get('content_id'),
            {
                'type': 'edit_change',
                'user_id': data.get('user_id'),
                'content_id': data.get('content_id'),
                'changes': data.get('changes'),
                'timestamp': datetime.now().isoformat()
            },
            exclude=[data.get('user_id')]
        )
    
    async def _handle_edit_end(self, client_id: str, data: Dict[str, Any]):
        """Handle edit session end."""
        await self._broadcast_to_content_subscribers(
            data.get('content_id'),
            {
                'type': 'edit_ended',
                'user_id': data.get('user_id'),
                'content_id': data.get('content_id'),
                'timestamp': datetime.now().isoformat()
            },
            exclude=[data.get('user_id')]
        )
    
    async def _handle_comment_add(self, client_id: str, data: Dict[str, Any]):
        """Handle new comment event."""
        await self._broadcast_to_content_subscribers(
            data.get('content_id'),
            {
                'type': 'comment_added',
                'comment': data.get('comment'),
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def _handle_comment_resolve(self, client_id: str, data: Dict[str, Any]):
        """Handle comment resolution."""
        await self._broadcast_to_content_subscribers(
            data.get('content_id'),
            {
                'type': 'comment_resolved',
                'comment_id': data.get('comment_id'),
                'resolved_by': data.get('user_id'),
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def _handle_cursor_move(self, client_id: str, data: Dict[str, Any]):
        """Handle cursor movement."""
        await self._broadcast_to_content_subscribers(
            data.get('content_id'),
            {
                'type': 'cursor_moved',
                'user_id': data.get('user_id'),
                'position': data.get('position'),
                'timestamp': datetime.now().isoformat()
            },
            exclude=[data.get('user_id')]
        )
    
    async def _handle_selection_change(self, client_id: str, data: Dict[str, Any]):
        """Handle selection change."""
        await self._broadcast_to_content_subscribers(
            data.get('content_id'),
            {
                'type': 'selection_changed',
                'user_id': data.get('user_id'),
                'selection': data.get('selection'),
                'timestamp': datetime.now().isoformat()
            },
            exclude=[data.get('user_id')]
        )
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client."""
        if client_id in self.connected_clients:
            try:
                await self.connected_clients[client_id].send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
    
    async def _send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user."""
        if user_id in self.user_sessions:
            client_id = self.user_sessions[user_id]
            await self._send_to_client(client_id, message)
    
    async def _broadcast_event(self, message: Dict[str, Any], exclude: List[str] = None):
        """Broadcast message to all connected users."""
        exclude = exclude or []
        
        for user_id, client_id in self.user_sessions.items():
            if user_id not in exclude:
                await self._send_to_client(client_id, message)
    
    async def _broadcast_to_content_subscribers(self, content_id: str, 
                                             message: Dict[str, Any], 
                                             exclude: List[str] = None):
        """Broadcast message to content subscribers."""
        if content_id not in self.content_subscribers:
            return
        
        exclude = exclude or []
        subscribers = self.content_subscribers[content_id]
        
        for user_id in subscribers:
            if user_id not in exclude:
                await self._send_to_user(user_id, message)

class CollaborationManager:
    """Main collaboration system manager."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the collaboration manager."""
        self.config = config
        self.db = CollaborationDatabase(config.get('db_path', './data/collaboration.db'))
        self.server = RealTimeCollaborationServer(
            host=config.get('host', 'localhost'),
            port=config.get('port', 8765)
        )
        
        # Active sessions tracking
        self.active_sessions: Dict[str, EditSession] = {}
        self.content_locks: Dict[str, Set[str]] = {}  # content_id -> set of locked sections
        
        logger.info("CollaborationManager initialized")
    
    async def start(self):
        """Start the collaboration system."""
        logger.info("Starting collaboration system")
        
        # Start the WebSocket server in background
        asyncio.create_task(self.server.start_server())
        
        # Start session cleanup task
        asyncio.create_task(self._cleanup_inactive_sessions())
    
    async def create_user(self, username: str, email: str, role: UserRole, 
                         display_name: str, **kwargs) -> Optional[User]:
        """Create a new user."""
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            role=role,
            display_name=display_name,
            **kwargs
        )
        
        success = await self.db.create_user(user)
        return user if success else None
    
    async def add_comment(self, content_id: str, content_type: ContentType,
                         user_id: str, text: str, comment_type: CommentType = CommentType.GENERAL,
                         position: Optional[Dict[str, Any]] = None,
                         thread_id: Optional[str] = None,
                         parent_comment_id: Optional[str] = None) -> Optional[Comment]:
        """Add a comment to content."""
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            content_id=content_id,
            content_type=content_type,
            user_id=user_id,
            comment_type=comment_type,
            text=text,
            timestamp=datetime.now(),
            position=position,
            thread_id=thread_id,
            parent_comment_id=parent_comment_id
        )
        
        success = await self.db.create_comment(comment)
        
        if success:
            # Broadcast to real-time subscribers
            await self.server._broadcast_to_content_subscribers(
                content_id,
                {
                    'type': 'comment_added',
                    'comment': asdict(comment),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return comment
        
        return None
    
    async def resolve_comment(self, comment_id: str, resolved_by: str) -> bool:
        """Resolve a comment."""
        # Implementation would update the database
        # For now, just broadcast the event
        await self.server._broadcast_event({
            'type': 'comment_resolved',
            'comment_id': comment_id,
            'resolved_by': resolved_by,
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    async def start_edit_session(self, content_id: str, content_type: ContentType,
                               user_id: str, sections: List[str] = None) -> Optional[EditSession]:
        """Start an editing session."""
        session = EditSession(
            session_id=str(uuid.uuid4()),
            content_id=content_id,
            content_type=content_type,
            user_id=user_id,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            locked_sections=set(sections or [])
        )
        
        # Check for conflicts
        if content_id in self.content_locks:
            existing_locks = self.content_locks[content_id]
            if session.locked_sections.intersection(existing_locks):
                logger.warning(f"Section lock conflict for content {content_id}")
                return None
        
        # Add session
        self.active_sessions[session.session_id] = session
        
        # Update content locks
        if content_id not in self.content_locks:
            self.content_locks[content_id] = set()
        self.content_locks[content_id].update(session.locked_sections)
        
        # Broadcast session start
        await self.server._broadcast_to_content_subscribers(
            content_id,
            {
                'type': 'edit_started',
                'session': asdict(session),
                'timestamp': datetime.now().isoformat()
            },
            exclude=[user_id]
        )
        
        return session
    
    async def end_edit_session(self, session_id: str) -> bool:
        """End an editing session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.is_active = False
        
        # Remove content locks
        if session.content_id in self.content_locks:
            self.content_locks[session.content_id] -= session.locked_sections
            if not self.content_locks[session.content_id]:
                del self.content_locks[session.content_id]
        
        # Broadcast session end
        await self.server._broadcast_to_content_subscribers(
            session.content_id,
            {
                'type': 'edit_ended',
                'session_id': session_id,
                'user_id': session.user_id,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return True
    
    async def create_approval_workflow(self, content_id: str, content_type: ContentType,
                                     created_by: str, steps: List[Dict[str, Any]],
                                     deadline: Optional[datetime] = None) -> ApprovalWorkflow:
        """Create an approval workflow."""
        workflow = ApprovalWorkflow(
            workflow_id=str(uuid.uuid4()),
            content_id=content_id,
            content_type=content_type,
            created_by=created_by,
            created_at=datetime.now(),
            deadline=deadline
        )
        
        # Create workflow steps
        for i, step_data in enumerate(steps):
            step = WorkflowStep(
                step_id=str(uuid.uuid4()),
                workflow_id=workflow.workflow_id,
                step_name=step_data['name'],
                step_order=i,
                required_role=UserRole(step_data['required_role']),
                required_users=step_data.get('required_users', [])
            )
            workflow.steps.append(step)
        
        # Save to database (implementation needed)
        # For now, just return the workflow
        
        return workflow
    
    async def advance_workflow(self, workflow_id: str, user_id: str, 
                             action: str, comments: str = "") -> bool:
        """Advance a workflow to the next step."""
        # Implementation would:
        # 1. Validate user permissions
        # 2. Update workflow status
        # 3. Notify next reviewers
        # 4. Broadcast workflow update
        
        await self.server._broadcast_event({
            'type': 'workflow_updated',
            'workflow_id': workflow_id,
            'action': action,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    async def get_content_comments(self, content_id: str, 
                                 content_type: ContentType) -> List[Comment]:
        """Get all comments for content."""
        return await self.db.get_comments(content_id, content_type)
    
    async def get_active_sessions(self, content_id: str) -> List[EditSession]:
        """Get active editing sessions for content."""
        return [
            session for session in self.active_sessions.values()
            if session.content_id == content_id and session.is_active
        ]
    
    async def _cleanup_inactive_sessions(self):
        """Periodically clean up inactive sessions."""
        while True:
            try:
                current_time = datetime.now()
                inactive_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    # Mark sessions inactive after 30 minutes of no activity
                    if (current_time - session.last_activity).total_seconds() > 1800:
                        inactive_sessions.append(session_id)
                
                # Clean up inactive sessions
                for session_id in inactive_sessions:
                    await self.end_edit_session(session_id)
                    logger.info(f"Cleaned up inactive session: {session_id}")
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

# Example usage
async def main():
    """Example usage of the collaboration system."""
    config = {
        'db_path': './data/collaboration.db',
        'host': 'localhost',
        'port': 8765
    }
    
    # Initialize collaboration manager
    manager = CollaborationManager(config)
    await manager.start()
    
    # Create test users
    admin_user = await manager.create_user(
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        display_name="System Administrator"
    )
    
    editor_user = await manager.create_user(
        username="editor1",
        email="editor1@example.com",
        role=UserRole.EDITOR,
        display_name="Content Editor"
    )
    
    if admin_user and editor_user:
        print(f"Created users: {admin_user.username}, {editor_user.username}")
        
        # Add a comment
        comment = await manager.add_comment(
            content_id="video_123",
            content_type=ContentType.VIDEO,
            user_id=editor_user.user_id,
            text="This section needs improvement",
            comment_type=CommentType.SUGGESTION
        )
        
        if comment:
            print(f"Added comment: {comment.comment_id}")
        
        # Start an edit session
        session = await manager.start_edit_session(
            content_id="video_123",
            content_type=ContentType.VIDEO,
            user_id=editor_user.user_id,
            sections=["intro", "main_content"]
        )
        
        if session:
            print(f"Started edit session: {session.session_id}")
            
            # End the session after some time
            await asyncio.sleep(2)
            await manager.end_edit_session(session.session_id)
            print("Ended edit session")

if __name__ == "__main__":
    asyncio.run(main())