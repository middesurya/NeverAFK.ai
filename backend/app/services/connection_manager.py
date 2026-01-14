"""
PRD-021: WebSocket Real-time Updates - Connection Manager Service

Manages WebSocket connections for real-time updates:
- Connection lifecycle (connect, disconnect, reconnect)
- Room/channel management for targeted broadcasting
- Message broadcasting (personal, room, global)
- Heartbeat/ping-pong for connection health
- User authentication binding

AC-1: WebSocket connection handling
AC-2: Message broadcasting support
AC-3: Room/channel management
AC-4: Connection lifecycle management
AC-5: Heartbeat/ping-pong mechanism
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import time
import uuid
import json
from enum import Enum
from datetime import datetime


class ConnectionState(Enum):
    """Connection state enum for tracking connection lifecycle."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class MessageType(Enum):
    """Message types for WebSocket communication."""
    PING = "ping"
    PONG = "pong"
    MESSAGE = "message"
    BROADCAST = "broadcast"
    ROOM_JOIN = "room_join"
    ROOM_LEAVE = "room_leave"
    ROOM_MESSAGE = "room_message"
    ERROR = "error"
    SYSTEM = "system"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"


@dataclass
class Connection:
    """
    Represents a WebSocket connection with associated metadata.

    Attributes:
        websocket: The WebSocket instance
        connection_id: Unique identifier for this connection
        user_id: Optional authenticated user ID
        rooms: Set of rooms this connection has joined
        state: Current connection state
        created_at: Connection creation timestamp
        last_ping: Last ping timestamp for heartbeat
        metadata: Additional connection metadata
    """
    websocket: WebSocket
    connection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    rooms: Set[str] = field(default_factory=set)
    state: ConnectionState = ConnectionState.CONNECTING
    created_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure rooms is a set."""
        if self.rooms is None:
            self.rooms = set()

    def to_dict(self) -> dict:
        """Convert connection info to dictionary (excluding websocket)."""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "rooms": list(self.rooms),
            "state": self.state.value,
            "created_at": self.created_at,
            "last_ping": self.last_ping,
            "metadata": self.metadata
        }


class ConnectionManager:
    """
    Manages WebSocket connections, rooms, and message broadcasting.

    Provides:
    - Connection lifecycle management (connect, disconnect)
    - Room/channel management (join, leave, list)
    - Message broadcasting (personal, room, global)
    - Heartbeat monitoring for connection health
    - User-to-connection mapping for targeted messaging
    """

    def __init__(self):
        """Initialize the connection manager."""
        self._connections: Dict[str, Connection] = {}
        self._rooms: Dict[str, Set[str]] = {}
        self._user_connections: Dict[str, Set[str]] = {}
        self._heartbeat_interval: float = 30.0  # seconds
        self._heartbeat_timeout: float = 60.0  # seconds
        self._max_connections_per_user: int = 5

    @property
    def connection_count(self) -> int:
        """Return total number of active connections."""
        return len(self._connections)

    @property
    def room_count(self) -> int:
        """Return total number of active rooms."""
        return len(self._rooms)

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by its ID."""
        return self._connections.get(connection_id)

    def get_connections_for_user(self, user_id: str) -> List[Connection]:
        """Get all connections for a specific user."""
        conn_ids = self._user_connections.get(user_id, set())
        return [self._connections[cid] for cid in conn_ids if cid in self._connections]

    def get_room_members(self, room: str) -> Set[str]:
        """Get all connection IDs in a room."""
        return self._rooms.get(room, set()).copy()

    def get_room_list(self) -> List[str]:
        """Get list of all active rooms."""
        return list(self._rooms.keys())

    def get_user_rooms(self, connection_id: str) -> Set[str]:
        """Get all rooms a connection has joined."""
        conn = self._connections.get(connection_id)
        return conn.rooms.copy() if conn else set()

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Connection:
        """
        Accept a WebSocket connection and register it.

        Args:
            websocket: The WebSocket to accept
            connection_id: Optional custom connection ID
            user_id: Optional user ID to bind to connection
            metadata: Optional connection metadata

        Returns:
            The created Connection object

        Raises:
            ValueError: If max connections per user exceeded
        """
        # Check user connection limit
        if user_id:
            existing_conns = self._user_connections.get(user_id, set())
            if len(existing_conns) >= self._max_connections_per_user:
                raise ValueError(
                    f"Maximum connections per user ({self._max_connections_per_user}) exceeded"
                )

        # Accept the WebSocket connection
        await websocket.accept()

        # Create connection object
        conn_id = connection_id or str(uuid.uuid4())
        connection = Connection(
            websocket=websocket,
            connection_id=conn_id,
            user_id=user_id,
            state=ConnectionState.CONNECTED,
            metadata=metadata or {}
        )

        # Register connection
        self._connections[conn_id] = connection

        # Map user to connection if user_id provided
        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(conn_id)

        return connection

    async def disconnect(self, connection_id: str) -> bool:
        """
        Disconnect and remove a WebSocket connection.

        Args:
            connection_id: The connection ID to disconnect

        Returns:
            True if connection was found and removed, False otherwise
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        # Update state
        connection.state = ConnectionState.DISCONNECTING

        # Remove from all rooms
        for room in list(connection.rooms):
            await self.leave_room(connection_id, room)

        # Remove from user mapping
        if connection.user_id and connection.user_id in self._user_connections:
            self._user_connections[connection.user_id].discard(connection_id)
            if not self._user_connections[connection.user_id]:
                del self._user_connections[connection.user_id]

        # Remove connection
        del self._connections[connection_id]

        return True

    async def join_room(self, connection_id: str, room: str) -> bool:
        """
        Add a connection to a room.

        Args:
            connection_id: The connection to add
            room: The room name to join

        Returns:
            True if successfully joined, False if connection not found
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        # Create room if it doesn't exist
        if room not in self._rooms:
            self._rooms[room] = set()

        # Add to room
        self._rooms[room].add(connection_id)
        connection.rooms.add(room)

        # Notify room members
        await self.broadcast_to_room(
            {
                "type": MessageType.USER_JOINED.value,
                "room": room,
                "connection_id": connection_id,
                "user_id": connection.user_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            room,
            exclude={connection_id}
        )

        return True

    async def leave_room(self, connection_id: str, room: str) -> bool:
        """
        Remove a connection from a room.

        Args:
            connection_id: The connection to remove
            room: The room name to leave

        Returns:
            True if successfully left, False if connection/room not found
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        if room not in self._rooms:
            return False

        # Remove from room
        self._rooms[room].discard(connection_id)
        connection.rooms.discard(room)

        # Notify room members
        await self.broadcast_to_room(
            {
                "type": MessageType.USER_LEFT.value,
                "room": room,
                "connection_id": connection_id,
                "user_id": connection.user_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            room
        )

        # Remove empty room
        if not self._rooms[room]:
            del self._rooms[room]

        return True

    async def send_personal(
        self,
        message: dict,
        connection_id: str,
        message_type: MessageType = MessageType.MESSAGE
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            message: The message payload
            connection_id: Target connection ID
            message_type: Type of message

        Returns:
            True if sent successfully, False otherwise
        """
        connection = self._connections.get(connection_id)
        if not connection or connection.state != ConnectionState.CONNECTED:
            return False

        try:
            payload = {
                "type": message_type.value,
                "data": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            await connection.websocket.send_json(payload)
            return True
        except Exception:
            return False

    async def send_to_user(
        self,
        message: dict,
        user_id: str,
        message_type: MessageType = MessageType.MESSAGE
    ) -> int:
        """
        Send a message to all connections of a specific user.

        Args:
            message: The message payload
            user_id: Target user ID
            message_type: Type of message

        Returns:
            Number of connections message was sent to
        """
        connections = self.get_connections_for_user(user_id)
        sent_count = 0

        for conn in connections:
            if await self.send_personal(message, conn.connection_id, message_type):
                sent_count += 1

        return sent_count

    async def broadcast_to_room(
        self,
        message: dict,
        room: str,
        exclude: Optional[Set[str]] = None,
        message_type: MessageType = MessageType.ROOM_MESSAGE
    ) -> int:
        """
        Broadcast a message to all connections in a room.

        Args:
            message: The message payload
            room: Target room name
            exclude: Connection IDs to exclude from broadcast
            message_type: Type of message

        Returns:
            Number of connections message was sent to
        """
        if room not in self._rooms:
            return 0

        exclude = exclude or set()
        sent_count = 0

        for conn_id in self._rooms[room]:
            if conn_id not in exclude:
                if await self.send_personal(message, conn_id, message_type):
                    sent_count += 1

        return sent_count

    async def broadcast(
        self,
        message: dict,
        exclude: Optional[Set[str]] = None,
        message_type: MessageType = MessageType.BROADCAST
    ) -> int:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message payload
            exclude: Connection IDs to exclude from broadcast
            message_type: Type of message

        Returns:
            Number of connections message was sent to
        """
        exclude = exclude or set()
        sent_count = 0

        for conn_id in list(self._connections.keys()):
            if conn_id not in exclude:
                if await self.send_personal(message, conn_id, message_type):
                    sent_count += 1

        return sent_count

    async def handle_ping(self, connection_id: str) -> bool:
        """
        Handle a ping message and send pong response.

        Args:
            connection_id: The connection sending ping

        Returns:
            True if pong sent successfully, False otherwise
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        # Update last ping time
        connection.last_ping = time.time()

        # Send pong
        return await self.send_personal(
            {"pong": True, "timestamp": time.time()},
            connection_id,
            MessageType.PONG
        )

    async def check_heartbeat(self, connection_id: str) -> bool:
        """
        Check if a connection's heartbeat is still valid.

        Args:
            connection_id: The connection to check

        Returns:
            True if heartbeat valid, False if timed out
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        elapsed = time.time() - connection.last_ping
        return elapsed < self._heartbeat_timeout

    async def cleanup_stale_connections(self) -> List[str]:
        """
        Remove connections that have timed out.

        Returns:
            List of connection IDs that were cleaned up
        """
        stale = []
        current_time = time.time()

        for conn_id, conn in list(self._connections.items()):
            if current_time - conn.last_ping > self._heartbeat_timeout:
                stale.append(conn_id)

        for conn_id in stale:
            await self.disconnect(conn_id)

        return stale

    async def send_error(
        self,
        connection_id: str,
        error_code: str,
        error_message: str
    ) -> bool:
        """
        Send an error message to a connection.

        Args:
            connection_id: Target connection
            error_code: Error code
            error_message: Human-readable error message

        Returns:
            True if sent successfully, False otherwise
        """
        return await self.send_personal(
            {"code": error_code, "message": error_message},
            connection_id,
            MessageType.ERROR
        )

    def bind_user(self, connection_id: str, user_id: str) -> bool:
        """
        Bind a user ID to an existing connection.

        Args:
            connection_id: The connection to bind
            user_id: The user ID to bind

        Returns:
            True if bound successfully, False if connection not found
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        # Remove old user binding if exists
        if connection.user_id and connection.user_id in self._user_connections:
            self._user_connections[connection.user_id].discard(connection_id)
            if not self._user_connections[connection.user_id]:
                del self._user_connections[connection.user_id]

        # Set new user binding
        connection.user_id = user_id
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection_id)

        return True

    def update_metadata(
        self,
        connection_id: str,
        metadata: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """
        Update connection metadata.

        Args:
            connection_id: The connection to update
            metadata: New metadata
            merge: If True, merge with existing; if False, replace

        Returns:
            True if updated successfully, False if connection not found
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        if merge:
            connection.metadata.update(metadata)
        else:
            connection.metadata = metadata

        return True

    def get_stats(self) -> dict:
        """Get connection manager statistics."""
        return {
            "total_connections": self.connection_count,
            "total_rooms": self.room_count,
            "total_users": len(self._user_connections),
            "rooms": {
                room: len(members)
                for room, members in self._rooms.items()
            }
        }


# Global singleton instance
connection_manager = ConnectionManager()
