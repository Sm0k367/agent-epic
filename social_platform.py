"""
Advanced Social Platform Architecture
Enables collaborative experiences, community interactions, and real-time social features
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import weakref
from abc import ABC, abstractmethod

class UserStatus(Enum):
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    INVISIBLE = "invisible"
    OFFLINE = "offline"

class ConnectionType(Enum):
    FRIEND = "friend"
    FOLLOWER = "follower"
    FOLLOWING = "following"
    BLOCKED = "blocked"
    MUTUAL = "mutual"

class RoomType(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INVITE_ONLY = "invite_only"
    TEMPORARY = "temporary"

class InteractionType(Enum):
    CHAT = "chat"
    VOICE = "voice"
    VIDEO = "video"
    GESTURE = "gesture"
    REACTION = "reaction"
    COLLABORATION = "collaboration"

class PrivacyLevel(Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"
    CUSTOM = "custom"

@dataclass
class UserProfile:
    """Comprehensive user profile with social features"""
    user_id: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    status: UserStatus = UserStatus.ONLINE
    preferences: Dict[str, Any] = field(default_factory=dict)
    privacy_settings: Dict[str, PrivacyLevel] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    achievements: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    hashed_password: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SocialConnection:
    """Represents a connection between two users"""
    connection_id: str
    user_id: str
    target_user_id: str
    connection_type: ConnectionType
    created_at: float
    strength: float = 0.5  # Connection strength (0.0 to 1.0)
    mutual: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SocialRoom:
    """Virtual room for social interactions"""
    room_id: str
    name: str
    description: str
    room_type: RoomType
    owner_id: str
    capacity: int
    current_users: Set[str] = field(default_factory=set)
    moderators: Set[str] = field(default_factory=set)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    """Social message with rich content support"""
    message_id: str
    sender_id: str
    room_id: Optional[str] = None
    recipient_id: Optional[str] = None
    content: str = ""
    message_type: str = "text"
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> user_ids
    timestamp: float = field(default_factory=time.time)
    edited_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SocialEvent:
    """Social platform event for real-time updates"""
    event_id: str
    event_type: str
    user_id: str
    room_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class EventHandler(ABC):
    """Abstract base class for event handlers"""
    
    @abstractmethod
    async def handle_event(self, event: SocialEvent) -> None:
        """Handle a social event"""
        pass

class UserManager:
    """Manages user profiles, authentication, and presence"""
    
    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.presence_callbacks: List[Callable] = []
    
    async def create_user(self, user_data: Dict[str, Any]) -> UserProfile:
        """Create a new user profile"""
        
        user_id = user_data.get("user_id", str(uuid.uuid4()))
        
        # Set default privacy settings
        default_privacy = {
            "profile": PrivacyLevel.PUBLIC,
            "status": PrivacyLevel.FRIENDS,
            "activity": PrivacyLevel.FRIENDS,
            "connections": PrivacyLevel.PRIVATE
        }
        
        user_profile = UserProfile(
            user_id=user_id,
            username=user_data["username"],
            display_name=user_data.get("display_name", user_data["username"]),
            avatar_url=user_data.get("avatar_url"),
            bio=user_data.get("bio"),
            preferences=user_data.get("preferences", {}),
            privacy_settings=user_data.get("privacy_settings", default_privacy),
            interests=user_data.get("interests", []),
            metadata=user_data.get("metadata", {})
        )
        
        self.users[user_id] = user_profile
        
        # Initialize session
        await self.create_session(user_id)
        
        return user_profile
    
    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        return self.users.get(user_id)
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserProfile]:
        """Update user profile"""
        
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        
        # Update allowed fields
        for field, value in updates.items():
            if hasattr(user, field) and field not in ["user_id", "created_at"]:
                setattr(user, field, value)
        
        # Update last active time
        user.last_active = time.time()
        
        # Notify presence change
        await self._notify_presence_change(user_id)
        
        return user
    
    async def set_user_status(self, user_id: str, status: UserStatus) -> bool:
        """Set user online status"""
        
        if user_id not in self.users:
            return False
        
        old_status = self.users[user_id].status
        self.users[user_id].status = status
        self.users[user_id].last_active = time.time()
        
        # Notify if status changed
        if old_status != status:
            await self._notify_presence_change(user_id)
        
        return True
    
    async def create_session(self, user_id: str) -> str:
        """Create a new user session"""
        
        session_id = str(uuid.uuid4())
        
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "metadata": {}
        }
        
        # Set user as online
        await self.set_user_status(user_id, UserStatus.ONLINE)
        
        return session_id
    
    async def end_session(self, session_id: str) -> bool:
        """End a user session"""
        
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        user_id = session["user_id"]
        
        # Remove session
        del self.active_sessions[session_id]
        
        # Check if user has other active sessions
        user_sessions = [s for s in self.active_sessions.values() if s["user_id"] == user_id]
        
        if not user_sessions:
            # Set user as offline if no other sessions
            await self.set_user_status(user_id, UserStatus.OFFLINE)
        
        return True
    
    async def get_online_users(self) -> List[UserProfile]:
        """Get list of online users"""
        
        return [
            user for user in self.users.values()
            if user.status in [UserStatus.ONLINE, UserStatus.AWAY, UserStatus.BUSY]
        ]
    
    async def search_users(self, query: str, filters: Dict[str, Any] = None) -> List[UserProfile]:
        """Search for users based on query and filters"""
        
        results = []
        query_lower = query.lower()
        
        for user in self.users.values():
            # Check if query matches username, display name, or bio
            if (query_lower in user.username.lower() or
                query_lower in user.display_name.lower() or
                (user.bio and query_lower in user.bio.lower())):
                
                # Apply filters if provided
                if filters:
                    if not self._user_matches_filters(user, filters):
                        continue
                
                results.append(user)
        
        return results
    
    def _user_matches_filters(self, user: UserProfile, filters: Dict[str, Any]) -> bool:
        """Check if user matches the provided filters"""
        
        for filter_key, filter_value in filters.items():
            if filter_key == "status":
                if user.status != UserStatus(filter_value):
                    return False
            elif filter_key == "interests":
                if not any(interest in user.interests for interest in filter_value):
                    return False
            elif filter_key == "online_only":
                if filter_value and user.status == UserStatus.OFFLINE:
                    return False
        
        return True
    
    async def _notify_presence_change(self, user_id: str):
        """Notify callbacks about presence changes"""
        
        user = self.users.get(user_id)
        if not user:
            return
        
        for callback in self.presence_callbacks:
            try:
                await callback(user_id, user.status)
            except Exception as e:
                print(f"Error in presence callback: {e}")
    
    def add_presence_callback(self, callback: Callable):
        """Add a callback for presence changes"""
        self.presence_callbacks.append(callback)

class ConnectionManager:
    """Manages social connections between users"""
    
    def __init__(self):
        self.connections: Dict[str, SocialConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
    
    async def create_connection(self, user_id: str, target_user_id: str, 
                              connection_type: ConnectionType) -> SocialConnection:
        """Create a new social connection"""
        
        connection_id = str(uuid.uuid4())
        
        connection = SocialConnection(
            connection_id=connection_id,
            user_id=user_id,
            target_user_id=target_user_id,
            connection_type=connection_type,
            created_at=time.time()
        )
        
        # Check for mutual connection
        reverse_connection = await self.get_connection(target_user_id, user_id)
        if reverse_connection and reverse_connection.connection_type == connection_type:
            connection.mutual = True
            reverse_connection.mutual = True
        
        self.connections[connection_id] = connection
        
        # Update user connections index
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        return connection
    
    async def get_connection(self, user_id: str, target_user_id: str) -> Optional[SocialConnection]:
        """Get connection between two users"""
        
        user_connection_ids = self.user_connections.get(user_id, set())
        
        for connection_id in user_connection_ids:
            connection = self.connections.get(connection_id)
            if connection and connection.target_user_id == target_user_id:
                return connection
        
        return None
    
    async def get_user_connections(self, user_id: str, 
                                 connection_type: Optional[ConnectionType] = None) -> List[SocialConnection]:
        """Get all connections for a user"""
        
        user_connection_ids = self.user_connections.get(user_id, set())
        connections = []
        
        for connection_id in user_connection_ids:
            connection = self.connections.get(connection_id)
            if connection:
                if connection_type is None or connection.connection_type == connection_type:
                    connections.append(connection)
        
        return connections
    
    async def update_connection_strength(self, connection_id: str, strength: float) -> bool:
        """Update connection strength based on interactions"""
        
        if connection_id not in self.connections:
            return False
        
        # Clamp strength between 0.0 and 1.0
        strength = max(0.0, min(1.0, strength))
        self.connections[connection_id].strength = strength
        
        return True
    
    async def remove_connection(self, connection_id: str) -> bool:
        """Remove a social connection"""
        
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        # Remove from connections
        del self.connections[connection_id]
        
        # Update user connections index
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
        
        return True
    
    async def get_mutual_connections(self, user_id: str, target_user_id: str) -> List[str]:
        """Get mutual connections between two users"""
        
        user_connections = await self.get_user_connections(user_id, ConnectionType.FRIEND)
        target_connections = await self.get_user_connections(target_user_id, ConnectionType.FRIEND)
        
        user_friends = {conn.target_user_id for conn in user_connections}
        target_friends = {conn.target_user_id for conn in target_connections}
        
        return list(user_friends.intersection(target_friends))
    
    async def suggest_connections(self, user_id: str, limit: int = 10) -> List[str]:
        """Suggest new connections based on mutual friends and interests"""
        
        suggestions = []
        user_connections = await self.get_user_connections(user_id, ConnectionType.FRIEND)
        user_friends = {conn.target_user_id for conn in user_connections}
        
        # Find friends of friends
        for friend_id in user_friends:
            friend_connections = await self.get_user_connections(friend_id, ConnectionType.FRIEND)
            
            for friend_conn in friend_connections:
                potential_friend = friend_conn.target_user_id
                
                # Skip if already connected or is the user themselves
                if potential_friend != user_id and potential_friend not in user_friends:
                    if potential_friend not in suggestions:
                        suggestions.append(potential_friend)
        
        return suggestions[:limit]

class RoomManager:
    """Manages social rooms and spaces"""
    
    def __init__(self):
        self.rooms: Dict[str, SocialRoom] = {}
        self.user_rooms: Dict[str, Set[str]] = {}  # user_id -> room_ids
        self.room_callbacks: List[Callable] = []
    
    async def create_room(self, room_data: Dict[str, Any]) -> SocialRoom:
        """Create a new social room"""
        
        room_id = room_data.get("room_id", str(uuid.uuid4()))
        
        room = SocialRoom(
            room_id=room_id,
            name=room_data["name"],
            description=room_data.get("description", ""),
            room_type=RoomType(room_data.get("room_type", "public")),
            owner_id=room_data["owner_id"],
            capacity=room_data.get("capacity", 50),
            settings=room_data.get("settings", {}),
            tags=room_data.get("tags", []),
            metadata=room_data.get("metadata", {})
        )
        
        # Add owner as moderator
        room.moderators.add(room.owner_id)
        
        self.rooms[room_id] = room
        
        return room
    
    async def get_room(self, room_id: str) -> Optional[SocialRoom]:
        """Get room by ID"""
        return self.rooms.get(room_id)
    
    async def join_room(self, room_id: str, user_id: str) -> bool:
        """Add user to room"""
        
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        # Check capacity
        if len(room.current_users) >= room.capacity:
            return False
        
        # Add user to room
        room.current_users.add(user_id)
        
        # Update user rooms index
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(room_id)
        
        # Notify room callbacks
        await self._notify_room_event("user_joined", room_id, user_id)
        
        return True
    
    async def leave_room(self, room_id: str, user_id: str) -> bool:
        """Remove user from room"""
        
        room = self.rooms.get(room_id)
        if not room or user_id not in room.current_users:
            return False
        
        # Remove user from room
        room.current_users.discard(user_id)
        room.moderators.discard(user_id)
        
        # Update user rooms index
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)
        
        # Notify room callbacks
        await self._notify_room_event("user_left", room_id, user_id)
        
        # Delete room if empty and temporary
        if (room.room_type == RoomType.TEMPORARY and 
            len(room.current_users) == 0):
            await self.delete_room(room_id)
        
        return True
    
    async def get_user_rooms(self, user_id: str) -> List[SocialRoom]:
        """Get all rooms a user is in"""
        
        user_room_ids = self.user_rooms.get(user_id, set())
        return [self.rooms[room_id] for room_id in user_room_ids if room_id in self.rooms]
    
    async def search_rooms(self, query: str, filters: Dict[str, Any] = None) -> List[SocialRoom]:
        """Search for rooms"""
        
        results = []
        query_lower = query.lower()
        
        for room in self.rooms.values():
            # Check if query matches name, description, or tags
            if (query_lower in room.name.lower() or
                query_lower in room.description.lower() or
                any(query_lower in tag.lower() for tag in room.tags)):
                
                # Apply filters if provided
                if filters:
                    if not self._room_matches_filters(room, filters):
                        continue
                
                results.append(room)
        
        return results
    
    def _room_matches_filters(self, room: SocialRoom, filters: Dict[str, Any]) -> bool:
        """Check if room matches the provided filters"""
        
        for filter_key, filter_value in filters.items():
            if filter_key == "room_type":
                if room.room_type != RoomType(filter_value):
                    return False
            elif filter_key == "has_space":
                if filter_value and len(room.current_users) >= room.capacity:
                    return False
            elif filter_key == "tags":
                if not any(tag in room.tags for tag in filter_value):
                    return False
        
        return True
    
    async def add_moderator(self, room_id: str, user_id: str, moderator_id: str) -> bool:
        """Add a moderator to a room"""
        
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        # Check if requester is owner or moderator
        if moderator_id != room.owner_id and moderator_id not in room.moderators:
            return False
        
        room.moderators.add(user_id)
        return True
    
    async def delete_room(self, room_id: str) -> bool:
        """Delete a room"""
        
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        # Remove all users from room
        for user_id in list(room.current_users):
            await self.leave_room(room_id, user_id)
        
        # Delete room
        del self.rooms[room_id]
        
        return True
    
    async def _notify_room_event(self, event_type: str, room_id: str, user_id: str):
        """Notify callbacks about room events"""
        
        for callback in self.room_callbacks:
            try:
                await callback(event_type, room_id, user_id)
            except Exception as e:
                print(f"Error in room callback: {e}")
    
    def add_room_callback(self, callback: Callable):
        """Add a callback for room events"""
        self.room_callbacks.append(callback)

class MessageManager:
    """Manages messaging and communication"""
    
    def __init__(self):
        self.messages: Dict[str, Message] = {}
        self.room_messages: Dict[str, List[str]] = {}  # room_id -> message_ids
        self.user_messages: Dict[str, List[str]] = {}  # user_id -> message_ids
        self.message_callbacks: List[Callable] = []
    
    async def send_message(self, message_data: Dict[str, Any]) -> Message:
        """Send a new message"""
        
        message_id = str(uuid.uuid4())
        
        message = Message(
            message_id=message_id,
            sender_id=message_data["sender_id"],
            room_id=message_data.get("room_id"),
            recipient_id=message_data.get("recipient_id"),
            content=message_data.get("content", ""),
            message_type=message_data.get("message_type", "text"),
            attachments=message_data.get("attachments", []),
            metadata=message_data.get("metadata", {})
        )
        
        self.messages[message_id] = message
        
        # Index message
        if message.room_id:
            if message.room_id not in self.room_messages:
                self.room_messages[message.room_id] = []
            self.room_messages[message.room_id].append(message_id)
        
        if message.recipient_id:
            if message.recipient_id not in self.user_messages:
                self.user_messages[message.recipient_id] = []
            self.user_messages[message.recipient_id].append(message_id)
        
        # Notify message callbacks
        await self._notify_message_event("message_sent", message)
        
        return message
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        return self.messages.get(message_id)
    
    async def get_room_messages(self, room_id: str, limit: int = 50, 
                               before_timestamp: Optional[float] = None) -> List[Message]:
        """Get messages from a room"""
        
        message_ids = self.room_messages.get(room_id, [])
        messages = []
        
        for message_id in reversed(message_ids):  # Most recent first
            message = self.messages.get(message_id)
            if message:
                if before_timestamp and message.timestamp >= before_timestamp:
                    continue
                messages.append(message)
                if len(messages) >= limit:
                    break
        
        return messages
    
    async def get_user_messages(self, user_id: str, limit: int = 50) -> List[Message]:
        """Get direct messages for a user"""
        
        message_ids = self.user_messages.get(user_id, [])
        messages = []
        
        for message_id in reversed(message_ids):  # Most recent first
            message = self.messages.get(message_id)
            if message:
                messages.append(message)
                if len(messages) >= limit:
                    break
        
        return messages
    
    async def add_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """Add reaction to a message"""
        
        message = self.messages.get(message_id)
        if not message:
            return False
        
        if emoji not in message.reactions:
            message.reactions[emoji] = []
        
        if user_id not in message.reactions[emoji]:
            message.reactions[emoji].append(user_id)
        
        # Notify message callbacks
        await self._notify_message_event("reaction_added", message)
        
        return True
    
    async def remove_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """Remove reaction from a message"""
        
        message = self.messages.get(message_id)
        if not message:
            return False
        
        if emoji in message.reactions and user_id in message.reactions[emoji]:
            message.reactions[emoji].remove(user_id)
            
            # Remove emoji if no users have reacted with it
            if not message.reactions[emoji]:
                del message.reactions[emoji]
            
            # Notify message callbacks
            await self._notify_message_event("reaction_removed", message)
            
            return True
        
        return False
    
    async def edit_message(self, message_id: str, new_content: str, user_id: str) -> bool:
        """Edit a message"""
        
        message = self.messages.get(message_id)
        if not message or message.sender_id != user_id:
            return False
        
        message.content = new_content
        message.edited_at = time.time()
        
        # Notify message callbacks
        await self._notify_message_event("message_edited", message)
        
        return True
    
    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message"""
        
        message = self.messages.get(message_id)
        if not message or message.sender_id != user_id:
            return False
        
        # Remove from indexes
        if message.room_id and message.room_id in self.room_messages:
            if message_id in self.room_messages[message.room_id]:
                self.room_messages[message.room_id].remove(message_id)
        
        if message.recipient_id and message.recipient_id in self.user_messages:
            if message_id in self.user_messages[message.recipient_id]:
                self.user_messages[message.recipient_id].remove(message_id)
        
        # Delete message
        del self.messages[message_id]
        
        # Notify message callbacks
        await self._notify_message_event("message_deleted", message)
        
        return True
    
    async def _notify_message_event(self, event_type: str, message: Message):
        """Notify callbacks about message events"""
        
        for callback in self.message_callbacks:
            try:
                await callback(event_type, message)
            except Exception as e:
                print(f"Error in message callback: {e}")
    
    def add_message_callback(self, callback: Callable):
        """Add a callback for message events"""
        self.message_callbacks.append(callback)

class RealtimeManager:
    """Manages real-time events and notifications"""
    
    def __init__(self):
        self.event_handlers: Dict[str, List[EventHandler]] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}  # user_id -> event_types
        self.room_subscriptions: Dict[str, Set[str]] = {}  # room_id -> user_ids
        self.event_queue: List[SocialEvent] = []
    
    async def subscribe_user(self, user_id: str, event_types: List[str]):
        """Subscribe user to event types"""
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        self.user_subscriptions[user_id].update(event_types)
    
    async def unsubscribe_user(self, user_id: str, event_types: List[str]):
        """Unsubscribe user from event types"""
        
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].difference_update(event_types)
    
    async def subscribe_to_room(self, user_id: str, room_id: str):
        """Subscribe user to room events"""
        
        if room_id not in self.room_subscriptions:
            self.room_subscriptions[room_id] = set()
        
        self.room_subscriptions[room_id].add(user_id)
    
    async def unsubscribe_from_room(self, user_id: str, room_id: str):
        """Unsubscribe user from room events"""
        
        if room_id in self.room_subscriptions:
            self.room_subscriptions[room_id].discard(user_id)
    
    async def emit_event(self, event: SocialEvent):
        """Emit a social event"""
        
        # Add to event queue
        self.event_queue.append(event)
        
        # Process event handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    await handler.handle_event(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
        
        # Notify subscribed users
        await self._notify_subscribers(event)
    
    async def _notify_subscribers(self, event: SocialEvent):
        """Notify users subscribed to this event type"""
        
        notified_users = set()
        
        # Notify users subscribed to this event type
        for user_id, subscriptions in self.user_subscriptions.items():
            if event.event_type in subscriptions:
                notified_users.add(user_id)
        
        # Notify users subscribed to the room
        if event.room_id and event.room_id in self.room_subscriptions:
            notified_users.update(self.room_subscriptions[event.room_id])
        
        # Send notifications (this would integrate with actual notification system)
        for user_id in notified_users:
            await self._send_notification(user_id, event)
    
    async def _send_notification(self, user_id: str, event: SocialEvent):
        """Send notification to user (placeholder for actual implementation)"""
        
        # This would integrate with WebSocket, push notifications, etc.
        print(f"Notification to {user_id}: {event.event_type}")
    
    def add_event_handler(self, event_type: str, handler: EventHandler):
        """Add an event handler for a specific event type"""
        
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
    
    async def get_recent_events(self, user_id: str, limit: int = 50) -> List[SocialEvent]:
        """Get recent events for a user"""
        
        user_subscriptions = self.user_subscriptions.get(user_id, set())
        relevant_events = []
        
        for event in reversed(self.event_queue):  # Most recent first
            if (event.event_type in user_subscriptions or 
                event.user_id == user_id or
                (event.room_id and event.room_id in self.room_subscriptions and 
                 user_id in self.room_subscriptions[event.room_id])):
                
                relevant_events.append(event)
                if len(relevant_events) >= limit:
                    break
        
        return relevant_events

class SocialPlatform:
    """
    Main social platform that orchestrates all social features
    Provides a unified interface for social interactions
    """
    
    def __init__(self):
        self.user_manager = UserManager()
        self.connection_manager = ConnectionManager()
        self.room_manager = RoomManager()
        self.message_manager = MessageManager()
        self.realtime_manager = RealtimeManager()
        
        # Set up cross-component callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Set up callbacks between components"""
        
        # User presence callbacks
        async def on_presence_change(user_id: str, status: UserStatus):
            event = SocialEvent(
                event_id=str(uuid.uuid4()),
                event_type="user_presence_changed",
                user_id=user_id,
                data={"status": status.value}
            )
            await self.realtime_manager.emit_event(event)
        
        self.user_manager.add_presence_callback(on_presence_change)
        
        # Room event callbacks
        async def on_room_event(event_type: str, room_id: str, user_id: str):
            event = SocialEvent(
                event_id=str(uuid.uuid4()),
                event_type=f"room_{event_type}",
                user_id=user_id,
                room_id=room_id
            )
            await self.realtime_manager.emit_event(event)
        
        self.room_manager.add_room_callback(on_room_event)
        
        # Message event callbacks
        async def on_message_event(event_type: str, message: Message):
            event = SocialEvent(
                event_id=str(uuid.uuid4()),
                event_type=f"message_{event_type}",
                user_id=message.sender_id,
                room_id=message.room_id,
                data={
                    "message_id": message.message_id,
                    "content": message.content,
                    "message_type": message.message_type
                }
            )
            await self.realtime_manager.emit_event(event)
        
        self.message_manager.add_message_callback(on_message_event)
    
    # User Management API
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user"""
        
        user = await self.user_manager.create_user(user_data)
        
        return {
            "success": True,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "status": user.status.value
            }
        }
    
    async def login_user(self, user_id: str) -> Dict[str, Any]:
        """Login a user and create session"""
        
        user = await self.user_manager.get_user(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        session_id = await self.user_manager.create_session(user_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "status": user.status.value
            }
        }
    
    async def logout_user(self, session_id: str) -> Dict[str, Any]:
        """Logout a user and end session"""
        
        success = await self.user_manager.end_session(session_id)
        
        return {"success": success}
    
    # Social Connection API
    async def send_friend_request(self, user_id: str, target_user_id: str) -> Dict[str, Any]:
        """Send a friend request"""
        
        # Check if users exist
        user = await self.user_manager.get_user(user_id)
        target_user = await self.user_manager.get_user(target_user_id)
        
        if not user or not target_user:
            return {"success": False, "error": "User not found"}
        
        # Check if connection already exists
        existing_connection = await self.connection_manager.get_connection(user_id, target_user_id)
        if existing_connection:
            return {"success": False, "error": "Connection already exists"}
        
        # Create friend connection
        connection = await self.connection_manager.create_connection(
            user_id, target_user_id, ConnectionType.FRIEND
        )
        
        # Emit event
        event = SocialEvent(
            event_id=str(uuid.uuid4()),
            event_type="friend_request_sent",
            user_id=user_id,
            data={"target_user_id": target_user_id}
        )
        await self.realtime_manager.emit_event(event)
        
        return {
            "success": True,
            "connection_id": connection.connection_id
        }
    
    async def get_user_friends(self, user_id: str) -> Dict[str, Any]:
        """Get user's friends list"""
        
        connections = await self.connection_manager.get_user_connections(
            user_id, ConnectionType.FRIEND
        )
        
        friends = []
        for connection in connections:
            friend = await self.user_manager.get_user(connection.target_user_id)
            if friend:
                friends.append({
                    "user_id": friend.user_id,
                    "username": friend.username,
                    "display_name": friend.display_name,
                    "status": friend.status.value,
                    "connection_strength": connection.strength,
                    "mutual": connection.mutual
                })
        
        return {
            "success": True,
            "friends": friends
        }
    
    # Room Management API
    async def create_room(self, room_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new social room"""
        
        room = await self.room_manager.create_room(room_data)
        
        # Auto-join the creator
        await self.room_manager.join_room(room.room_id, room.owner_id)
        
        return {
            "success": True,
            "room": {
                "room_id": room.room_id,
                "name": room.name,
                "description": room.description,
                "room_type": room.room_type.value,
                "capacity": room.capacity,
                "current_users": len(room.current_users)
            }
        }
    
    async def join_room(self, room_id: str, user_id: str) -> Dict[str, Any]:
        """Join a social room"""
        
        success = await self.room_manager.join_room(room_id, user_id)
        
        if success:
            # Subscribe to room events
            await self.realtime_manager.subscribe_to_room(user_id, room_id)
        
        return {"success": success}
    
    async def leave_room(self, room_id: str, user_id: str) -> Dict[str, Any]:
        """Leave a social room"""
        
        success = await self.room_manager.leave_room(room_id, user_id)
        
        if success:
            # Unsubscribe from room events
            await self.realtime_manager.unsubscribe_from_room(user_id, room_id)
        
        return {"success": success}
    
    async def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """Get room information"""
        
        room = await self.room_manager.get_room(room_id)
        if not room:
            return {"success": False, "error": "Room not found"}
        
        # Get user info for current users
        users = []
        for user_id in room.current_users:
            user = await self.user_manager.get_user(user_id)
            if user:
                users.append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "display_name": user.display_name,
                    "status": user.status.value
                })
        
        return {
            "success": True,
            "room": {
                "room_id": room.room_id,
                "name": room.name,
                "description": room.description,
                "room_type": room.room_type.value,
                "owner_id": room.owner_id,
                "capacity": room.capacity,
                "current_users": users,
                "moderators": list(room.moderators),
                "tags": room.tags
            }
        }
    
    # Messaging API
    async def send_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message"""
        
        message = await self.message_manager.send_message(message_data)
        
        return {
            "success": True,
            "message": {
                "message_id": message.message_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "timestamp": message.timestamp
            }
        }
    
    async def get_room_messages(self, room_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get messages from a room"""
        
        messages = await self.message_manager.get_room_messages(room_id, limit)
        
        message_list = []
        for message in messages:
            sender = await self.user_manager.get_user(message.sender_id)
            message_list.append({
                "message_id": message.message_id,
                "sender": {
                    "user_id": sender.user_id,
                    "username": sender.username,
                    "display_name": sender.display_name
                } if sender else None,
                "content": message.content,
                "message_type": message.message_type,
                "timestamp": message.timestamp,
                "reactions": message.reactions
            })
        
        return {
            "success": True,
            "messages": message_list
        }
    
    # Search and Discovery API
    async def search_users(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for users"""
        
        users = await self.user_manager.search_users(query, filters)
        
        user_list = []
        for user in users:
            user_list.append({
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "status": user.status.value,
                "bio": user.bio,
                "interests": user.interests
            })
        
        return {
            "success": True,
            "users": user_list
        }
    
    async def search_rooms(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for rooms"""
        
        rooms = await self.room_manager.search_rooms(query, filters)
        
        room_list = []
        for room in rooms:
            room_list.append({
                "room_id": room.room_id,
                "name": room.name,
                "description": room.description,
                "room_type": room.room_type.value,
                "current_users": len(room.current_users),
                "capacity": room.capacity,
                "tags": room.tags
            })
        
        return {
            "success": True,
            "rooms": room_list
        }
    
    async def get_suggestions(self, user_id: str) -> Dict[str, Any]:
        """Get personalized suggestions for a user"""
        
        # Get friend suggestions
        friend_suggestions = await self.connection_manager.suggest_connections(user_id)
        
        # Get suggested users info
        suggested_users = []
        for suggested_user_id in friend_suggestions:
            user = await self.user_manager.get_user(suggested_user_id)
            if user:
                mutual_friends = await self.connection_manager.get_mutual_connections(
                    user_id, suggested_user_id
                )
                suggested_users.append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "display_name": user.display_name,
                    "mutual_friends_count": len(mutual_friends),
                    "common_interests": []  # Could be calculated based on interests
                })
        
        return {
            "success": True,
            "friend_suggestions": suggested_users
        }

# Example usage and demonstration
async def demo_social_platform():
    """Demonstrate the Social Platform capabilities"""
    
    # Create social platform
    platform = SocialPlatform()
    
    # Register users
    user1_data = {
        "username": "alice_wonder",
        "display_name": "Alice",
        "bio": "Love exploring virtual worlds",
        "interests": ["gaming", "art", "music"]
    }
    
    user2_data = {
        "username": "bob_builder",
        "display_name": "Bob",
        "bio": "Creative developer and designer",
        "interests": ["technology", "design", "music"]
    }
    
    user1_result = await platform.register_user(user1_data)
    user2_result = await platform.register_user(user2_data)
    
    user1_id = user1_result["user"]["user_id"]
    user2_id = user2_result["user"]["user_id"]
    
    print("Social Platform Demo")
    print("=" * 40)
    print(f"Registered users: {user1_result['user']['username']}, {user2_result['user']['username']}")
    
    # Send friend request
    friend_request = await platform.send_friend_request(user1_id, user2_id)
    print(f"Friend request sent: {friend_request['success']}")
    
    # Create a room
    room_data = {
        "name": "Creative Lounge",
        "description": "A space for creative minds to connect",
        "room_type": "public",
        "owner_id": user1_id,
        "capacity": 10,
        "tags": ["creative", "art", "collaboration"]
    }
    
    room_result = await platform.create_room(room_data)
    room_id = room_result["room"]["room_id"]
    print(f"Created room: {room_result['room']['name']}")
    
    # Join room
    join_result = await platform.join_room(room_id, user2_id)
    print(f"User joined room: {join_result['success']}")
    
    # Send messages
    message1 = await platform.send_message({
        "sender_id": user1_id,
        "room_id": room_id,
        "content": "Welcome to the Creative Lounge!",
        "message_type": "text"
    })
    
    message2 = await platform.send_message({
        "sender_id": user2_id,
        "room_id": room_id,
        "content": "Thanks! Excited to be here!",
        "message_type": "text"
    })
    
    print(f"Messages sent: {message1['success']}, {message2['success']}")
    
    # Get room messages
    messages_result = await platform.get_room_messages(room_id)
    print(f"Retrieved {len(messages_result['messages'])} messages")
    
    # Search functionality
    user_search = await platform.search_users("alice")
    room_search = await platform.search_rooms("creative")
    
    print(f"User search results: {len(user_search['users'])}")
    print(f"Room search results: {len(room_search['rooms'])}")
    
    # Get suggestions
    suggestions = await platform.get_suggestions(user1_id)
    print(f"Friend suggestions: {len(suggestions['friend_suggestions'])}")
    
    return {
        "platform": platform,
        "users": [user1_id, user2_id],
        "room_id": room_id,
        "messages": messages_result['messages']
    }

if __name__ == "__main__":
    # Run the demo
    demo_result = asyncio.run(demo_social_platform())
    
    print("\nSocial Platform Demo completed successfully!")
    print(f"Platform created with {len(demo_result['users'])} users")
    print(f"Room created: {demo_result['room_id']}")
    print(f"Messages exchanged: {len(demo_result['messages'])}")