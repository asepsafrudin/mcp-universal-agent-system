#!/usr/bin/env python3
"""
Real-time Collaboration System untuk CrewAI Documentation
Menyediakan WebSocket communication untuk status updates dan multi-user collaboration
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from websockets.server import serve
from pathlib import Path

class EventType(Enum):
    """Types of real-time events"""
    STATUS_UPDATE = "status_update"
    PROGRESS_UPDATE = "progress_update"
    DOCUMENT_EDIT = "document_edit"
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    SYSTEM_MESSAGE = "system_message"
    AGENT_STATUS = "agent_status"
    WORKFLOW_UPDATE = "workflow_update"

@dataclass
class CollaborationEvent:
    """Represents a collaboration event"""
    event_type: EventType
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    data: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "data": self.data or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationEvent':
        """Create from dictionary"""
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            data=data.get("data", {})
        )

class RealTimeCollaboration:
    """
    Real-time collaboration system for CrewAI documentation
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize collaboration system
        
        Args:
            host: WebSocket server host
            port: WebSocket server port
        """
        self.host = host
        self.port = port
        
        # Active connections
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Set[str]] = {}  # session_id -> set of user_ids
        
        # Event history for new connections
        self.event_history: List[CollaborationEvent] = []
        self.max_history = 100
        
        # Workflow state
        self.workflow_state = {
            "current_phase": "idle",
            "progress": 0,
            "agents_status": {
                "researcher": "waiting",
                "writer": "waiting", 
                "checker": "waiting"
            },
            "started_at": None,
            "estimated_completion": None
        }
    
    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        user_id = None
        session_id = None
        
        try:
            # Wait for initial handshake
            welcome_msg = {
                "type": "welcome",
                "message": "Connected to CrewAI Collaboration Server",
                "timestamp": datetime.now().isoformat(),
                "server_info": {
                    "version": "1.0.0",
                    "capabilities": ["real-time-updates", "multi-user", "document-editing"]
                }
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.process_message(websocket, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON")
                except Exception as e:
                    await self.send_error(websocket, f"Processing error: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Clean up connection
            if user_id:
                await self.handle_user_leave(user_id, session_id)
    
    async def process_message(self, websocket, data: Dict[str, Any]):
        """Process incoming message"""
        msg_type = data.get("type")
        
        if msg_type == "handshake":
            await self.handle_handshake(websocket, data)
        elif msg_type == "status_request":
            await self.send_current_status(websocket)
        elif msg_type == "document_edit":
            await self.handle_document_edit(websocket, data)
        elif msg_type == "user_action":
            await self.handle_user_action(websocket, data)
        else:
            await self.send_error(websocket, f"Unknown message type: {msg_type}")
    
    async def handle_handshake(self, websocket, data: Dict[str, Any]):
        """Handle user handshake"""
        user_id = data.get("user_id", f"user_{int(time.time())}")
        session_id = data.get("session_id", "default")
        
        # Store connection
        self.connections[user_id] = websocket
        
        # Add user info
        self.users[user_id] = {
            "id": user_id,
            "name": data.get("name", f"User {len(self.users) + 1}"),
            "role": data.get("role", "viewer"),
            "connected_at": datetime.now(),
            "session_id": session_id
        }
        
        # Add to session
        if session_id not in self.sessions:
            self.sessions[session_id] = set()
        self.sessions[session_id].add(user_id)
        
        # Notify others
        join_event = CollaborationEvent(
            event_type=EventType.USER_JOIN,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            data=self.users[user_id]
        )
        await self.broadcast_event(join_event, exclude_user=user_id)
        
        # Send recent history to new user
        await self.send_event_history(websocket)
        
        # Update workflow status if needed
        await self.broadcast_workflow_status()
    
    async def handle_user_leave(self, user_id: str, session_id: Optional[str]):
        """Handle user disconnection"""
        # Remove from connections
        if user_id in self.connections:
            del self.connections[user_id]
        
        # Remove user info
        if user_id in self.users:
            user_info = self.users[user_id]
            session_id = session_id or user_info.get("session_id")
            del self.users[user_id]
        
        # Remove from session
        if session_id and session_id in self.sessions:
            self.sessions[session_id].discard(user_id)
            if not self.sessions[session_id]:
                del self.sessions[session_id]
        
        # Notify others
        leave_event = CollaborationEvent(
            event_type=EventType.USER_LEAVE,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            data={"reason": "disconnection"}
        )
        await self.broadcast_event(leave_event)
    
    async def send_current_status(self, websocket):
        """Send current system status to user"""
        status = {
            "type": "system_status",
            "data": {
                "workflow_state": self.workflow_state,
                "active_users": len(self.users),
                "sessions": {sid: len(users) for sid, users in self.sessions.items()},
                "server_time": datetime.now().isoformat()
            }
        }
        await websocket.send(json.dumps(status))
    
    async def handle_document_edit(self, websocket, data: Dict[str, Any]):
        """Handle document editing events"""
        user_id = data.get("user_id")
        if not user_id or user_id not in self.users:
            return
        
        edit_event = CollaborationEvent(
            event_type=EventType.DOCUMENT_EDIT,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=self.users[user_id].get("session_id"),
            data={
                "document": data.get("document"),
                "changes": data.get("changes"),
                "position": data.get("position"),
                "operation": data.get("operation")
            }
        )
        
        await self.broadcast_event(edit_event, exclude_user=user_id)
    
    async def handle_user_action(self, websocket, data: Dict[str, Any]):
        """Handle user actions like starting workflow"""
        user_id = data.get("user_id")
        action = data.get("action")
        
        if action == "start_workflow":
            await self.start_workflow(user_id)
        elif action == "pause_workflow":
            await self.pause_workflow(user_id)
        elif action == "resume_workflow":
            await self.resume_workflow(user_id)
    
    async def start_workflow(self, user_id: str):
        """Start the documentation workflow"""
        self.workflow_state.update({
            "current_phase": "research",
            "progress": 0,
            "started_at": datetime.now(),
            "agents_status": {
                "researcher": "active",
                "writer": "waiting",
                "checker": "waiting"
            }
        })
        
        start_event = CollaborationEvent(
            event_type=EventType.WORKFLOW_UPDATE,
            timestamp=datetime.now(),
            user_id=user_id,
            data=self.workflow_state
        )
        await self.broadcast_event(start_event)
    
    async def pause_workflow(self, user_id: str):
        """Pause the workflow"""
        self.workflow_state["current_phase"] = "paused"
        self.workflow_state["agents_status"] = {
            "researcher": "paused",
            "writer": "paused",
            "checker": "paused"
        }
        
        pause_event = CollaborationEvent(
            event_type=EventType.WORKFLOW_UPDATE,
            timestamp=datetime.now(),
            user_id=user_id,
            data=self.workflow_state
        )
        await self.broadcast_event(pause_event)
    
    async def resume_workflow(self, user_id: str):
        """Resume the workflow"""
        if "paused" in self.workflow_state["current_phase"]:
            self.workflow_state["current_phase"] = "research"
            self.workflow_state["agents_status"]["researcher"] = "active"
        
        resume_event = CollaborationEvent(
            event_type=EventType.WORKFLOW_UPDATE,
            timestamp=datetime.now(),
            user_id=user_id,
            data=self.workflow_state
        )
        await self.broadcast_event(resume_event)
    
    async def update_agent_status(self, agent_name: str, status: str, progress: Optional[int] = None):
        """Update agent status and broadcast"""
        self.workflow_state["agents_status"][agent_name] = status
        if progress is not None:
            self.workflow_state["progress"] = progress
        
        status_event = CollaborationEvent(
            event_type=EventType.AGENT_STATUS,
            timestamp=datetime.now(),
            data={
                "agent": agent_name,
                "status": status,
                "progress": progress,
                "overall_progress": self.workflow_state["progress"]
            }
        )
        await self.broadcast_event(status_event)
    
    async def send_progress_update(self, phase: str, progress: int, message: str):
        """Send progress update"""
        progress_event = CollaborationEvent(
            event_type=EventType.PROGRESS_UPDATE,
            timestamp=datetime.now(),
            data={
                "phase": phase,
                "progress": progress,
                "message": message
            }
        )
        await self.broadcast_event(progress_event)
    
    async def broadcast_event(self, event: CollaborationEvent, exclude_user: Optional[str] = None):
        """Broadcast event to all connected users"""
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Send to all users
        message = {
            "type": "event",
            "event": event.to_dict()
        }
        
        disconnected_users = []
        for user_id, websocket in self.connections.items():
            if user_id != exclude_user:
                try:
                    await websocket.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.handle_user_leave(user_id, None)
    
    async def send_event_history(self, websocket):
        """Send recent event history to user"""
        recent_events = self.event_history[-20:]  # Last 20 events
        history_message = {
            "type": "event_history",
            "events": [event.to_dict() for event in recent_events]
        }
        await websocket.send(json.dumps(history_message))
    
    async def send_error(self, websocket, error_message: str):
        """Send error message to user"""
        error_msg = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(error_msg))
    
    async def broadcast_workflow_status(self):
        """Broadcast current workflow status to all users"""
        status_message = {
            "type": "workflow_status",
            "data": self.workflow_state
        }
        
        for websocket in self.connections.values():
            try:
                await websocket.send(json.dumps(status_message))
            except websockets.exceptions.ConnectionClosed:
                pass
    
    async def start_server(self):
        """Start the WebSocket server"""
        print(f"🚀 Starting Real-time Collaboration Server...")
        print(f"📡 WebSocket Server: ws://{self.host}:{self.port}")
        print(f"👥 Max concurrent users: {len(self.connections)}")
        
        async with serve(self.handle_connection, self.host, self.port):
            print("✅ Collaboration server is running...")
            await asyncio.Future()  # Run forever

# Global collaboration instance
collaboration = RealTimeCollaboration()

def get_collaboration_system() -> RealTimeCollaboration:
    """Get global collaboration system instance"""
    return collaboration

async def start_collaboration_server(host: str = "localhost", port: int = 8765):
    """Start the collaboration server"""
    global collaboration
    collaboration = RealTimeCollaboration(host, port)
    await collaboration.start_server()

if __name__ == "__main__":
    # Test collaboration system
    print("🌐 Testing Real-time Collaboration System...")
    
    # Start server
    asyncio.run(start_collaboration_server())
