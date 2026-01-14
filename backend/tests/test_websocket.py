"""
PRD-021: WebSocket Real-time Updates - Comprehensive Tests

Tests for WebSocket functionality:
- Connection Manager service tests
- WebSocket endpoint integration tests
- Room/channel management tests
- Message broadcasting tests
- Heartbeat/ping-pong tests
- Connection lifecycle tests

35+ tests covering all acceptance criteria.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from dataclasses import dataclass
from typing import Set

# Import the modules under test
from app.services.connection_manager import (
    ConnectionManager,
    Connection,
    ConnectionState,
    MessageType,
    connection_manager
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def manager():
    """Create a fresh ConnectionManager instance for each test."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket object."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def mock_websocket_factory():
    """Factory to create multiple mock WebSocket objects."""
    def _create():
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        ws.receive_text = AsyncMock()
        ws.close = AsyncMock()
        return ws
    return _create


# =============================================================================
# CONNECTION CLASS TESTS
# =============================================================================

class TestConnectionDataclass:
    """Tests for the Connection dataclass."""

    def test_connection_default_values(self, mock_websocket):
        """Connection should have sensible defaults."""
        conn = Connection(websocket=mock_websocket)

        assert conn.websocket == mock_websocket
        assert conn.connection_id is not None
        assert conn.user_id is None
        assert isinstance(conn.rooms, set)
        assert len(conn.rooms) == 0
        assert conn.state == ConnectionState.CONNECTING
        assert conn.created_at > 0
        assert conn.last_ping > 0
        assert isinstance(conn.metadata, dict)

    def test_connection_custom_values(self, mock_websocket):
        """Connection should accept custom values."""
        conn = Connection(
            websocket=mock_websocket,
            connection_id="test-123",
            user_id="user-456",
            rooms={"room1", "room2"},
            state=ConnectionState.CONNECTED,
            metadata={"key": "value"}
        )

        assert conn.connection_id == "test-123"
        assert conn.user_id == "user-456"
        assert "room1" in conn.rooms
        assert "room2" in conn.rooms
        assert conn.state == ConnectionState.CONNECTED
        assert conn.metadata["key"] == "value"

    def test_connection_to_dict(self, mock_websocket):
        """Connection.to_dict should exclude websocket."""
        conn = Connection(
            websocket=mock_websocket,
            connection_id="test-123",
            user_id="user-456",
            rooms={"room1"}
        )

        data = conn.to_dict()

        assert "websocket" not in data
        assert data["connection_id"] == "test-123"
        assert data["user_id"] == "user-456"
        assert "room1" in data["rooms"]
        assert data["state"] == ConnectionState.CONNECTING.value

    def test_connection_rooms_none_initialization(self, mock_websocket):
        """Connection should handle None rooms gracefully."""
        conn = Connection(websocket=mock_websocket, rooms=None)
        assert isinstance(conn.rooms, set)


# =============================================================================
# CONNECTION MANAGER - BASIC OPERATIONS TESTS
# =============================================================================

class TestConnectionManagerBasic:
    """Tests for basic ConnectionManager operations."""

    def test_manager_initialization(self, manager):
        """Manager should initialize with empty state."""
        assert manager.connection_count == 0
        assert manager.room_count == 0

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager, mock_websocket):
        """Connect should accept the websocket."""
        conn = await manager.connect(mock_websocket)

        mock_websocket.accept.assert_called_once()
        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_connect_returns_connection(self, manager, mock_websocket):
        """Connect should return a Connection object."""
        conn = await manager.connect(mock_websocket)

        assert isinstance(conn, Connection)
        assert conn.state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_connect_with_custom_id(self, manager, mock_websocket):
        """Connect should use provided connection ID."""
        conn = await manager.connect(mock_websocket, connection_id="custom-id")

        assert conn.connection_id == "custom-id"

    @pytest.mark.asyncio
    async def test_connect_with_user_id(self, manager, mock_websocket):
        """Connect should bind user ID."""
        conn = await manager.connect(mock_websocket, user_id="user-123")

        assert conn.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_connect_with_metadata(self, manager, mock_websocket):
        """Connect should store metadata."""
        conn = await manager.connect(
            mock_websocket,
            metadata={"device": "mobile"}
        )

        assert conn.metadata["device"] == "mobile"

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager, mock_websocket):
        """Disconnect should remove the connection."""
        conn = await manager.connect(mock_websocket)
        conn_id = conn.connection_id

        result = await manager.disconnect(conn_id)

        assert result is True
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_returns_false(self, manager):
        """Disconnect should return False for unknown connection."""
        result = await manager.disconnect("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_connection(self, manager, mock_websocket):
        """Get connection should return the connection."""
        conn = await manager.connect(mock_websocket)

        retrieved = manager.get_connection(conn.connection_id)

        assert retrieved == conn

    def test_get_connection_nonexistent(self, manager):
        """Get connection should return None for unknown ID."""
        result = manager.get_connection("nonexistent")

        assert result is None


# =============================================================================
# CONNECTION MANAGER - USER BINDING TESTS
# =============================================================================

class TestConnectionManagerUserBinding:
    """Tests for user-to-connection binding."""

    @pytest.mark.asyncio
    async def test_user_connection_mapping(self, manager, mock_websocket):
        """User connections should be tracked."""
        conn = await manager.connect(mock_websocket, user_id="user-123")

        connections = manager.get_connections_for_user("user-123")

        assert len(connections) == 1
        assert connections[0] == conn

    @pytest.mark.asyncio
    async def test_multiple_connections_per_user(
        self, manager, mock_websocket_factory
    ):
        """User can have multiple connections."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        await manager.connect(ws1, user_id="user-123")
        await manager.connect(ws2, user_id="user-123")

        connections = manager.get_connections_for_user("user-123")

        assert len(connections) == 2

    @pytest.mark.asyncio
    async def test_max_connections_per_user(
        self, manager, mock_websocket_factory
    ):
        """Should enforce max connections per user."""
        manager._max_connections_per_user = 2

        await manager.connect(mock_websocket_factory(), user_id="user-123")
        await manager.connect(mock_websocket_factory(), user_id="user-123")

        with pytest.raises(ValueError, match="Maximum connections"):
            await manager.connect(mock_websocket_factory(), user_id="user-123")

    @pytest.mark.asyncio
    async def test_disconnect_removes_user_mapping(
        self, manager, mock_websocket
    ):
        """Disconnect should clean up user mapping."""
        conn = await manager.connect(mock_websocket, user_id="user-123")
        await manager.disconnect(conn.connection_id)

        connections = manager.get_connections_for_user("user-123")

        assert len(connections) == 0

    @pytest.mark.asyncio
    async def test_bind_user_to_connection(self, manager, mock_websocket):
        """Can bind user to existing connection."""
        conn = await manager.connect(mock_websocket)
        assert conn.user_id is None

        result = manager.bind_user(conn.connection_id, "user-456")

        assert result is True
        assert conn.user_id == "user-456"
        connections = manager.get_connections_for_user("user-456")
        assert len(connections) == 1

    def test_bind_user_nonexistent_connection(self, manager):
        """Bind user should fail for unknown connection."""
        result = manager.bind_user("nonexistent", "user-123")

        assert result is False


# =============================================================================
# CONNECTION MANAGER - ROOM MANAGEMENT TESTS
# =============================================================================

class TestConnectionManagerRooms:
    """Tests for room/channel management."""

    @pytest.mark.asyncio
    async def test_join_room(self, manager, mock_websocket):
        """Connection should be able to join a room."""
        conn = await manager.connect(mock_websocket)

        result = await manager.join_room(conn.connection_id, "test-room")

        assert result is True
        assert "test-room" in conn.rooms
        assert manager.room_count == 1

    @pytest.mark.asyncio
    async def test_join_multiple_rooms(self, manager, mock_websocket):
        """Connection should be able to join multiple rooms."""
        conn = await manager.connect(mock_websocket)

        await manager.join_room(conn.connection_id, "room1")
        await manager.join_room(conn.connection_id, "room2")

        assert len(conn.rooms) == 2
        assert "room1" in conn.rooms
        assert "room2" in conn.rooms

    @pytest.mark.asyncio
    async def test_join_room_nonexistent_connection(self, manager):
        """Join room should fail for unknown connection."""
        result = await manager.join_room("nonexistent", "room1")

        assert result is False

    @pytest.mark.asyncio
    async def test_leave_room(self, manager, mock_websocket):
        """Connection should be able to leave a room."""
        conn = await manager.connect(mock_websocket)
        await manager.join_room(conn.connection_id, "test-room")

        result = await manager.leave_room(conn.connection_id, "test-room")

        assert result is True
        assert "test-room" not in conn.rooms

    @pytest.mark.asyncio
    async def test_leave_room_removes_empty_room(self, manager, mock_websocket):
        """Leaving last member should remove room."""
        conn = await manager.connect(mock_websocket)
        await manager.join_room(conn.connection_id, "test-room")
        assert manager.room_count == 1

        await manager.leave_room(conn.connection_id, "test-room")

        assert manager.room_count == 0

    @pytest.mark.asyncio
    async def test_get_room_members(self, manager, mock_websocket_factory):
        """Get room members should return all members."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        conn1 = await manager.connect(ws1)
        conn2 = await manager.connect(ws2)

        await manager.join_room(conn1.connection_id, "test-room")
        await manager.join_room(conn2.connection_id, "test-room")

        members = manager.get_room_members("test-room")

        assert len(members) == 2
        assert conn1.connection_id in members
        assert conn2.connection_id in members

    def test_get_room_members_empty(self, manager):
        """Get room members should return empty set for unknown room."""
        members = manager.get_room_members("nonexistent")

        assert len(members) == 0

    @pytest.mark.asyncio
    async def test_get_user_rooms(self, manager, mock_websocket):
        """Get user rooms should return all joined rooms."""
        conn = await manager.connect(mock_websocket)
        await manager.join_room(conn.connection_id, "room1")
        await manager.join_room(conn.connection_id, "room2")

        rooms = manager.get_user_rooms(conn.connection_id)

        assert len(rooms) == 2
        assert "room1" in rooms
        assert "room2" in rooms

    @pytest.mark.asyncio
    async def test_disconnect_leaves_all_rooms(
        self, manager, mock_websocket_factory
    ):
        """Disconnect should remove connection from all rooms."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        conn1 = await manager.connect(ws1)
        conn2 = await manager.connect(ws2)

        await manager.join_room(conn1.connection_id, "room1")
        await manager.join_room(conn2.connection_id, "room1")

        await manager.disconnect(conn1.connection_id)

        members = manager.get_room_members("room1")
        assert conn1.connection_id not in members
        assert conn2.connection_id in members


# =============================================================================
# CONNECTION MANAGER - MESSAGE SENDING TESTS
# =============================================================================

class TestConnectionManagerMessaging:
    """Tests for message sending functionality."""

    @pytest.mark.asyncio
    async def test_send_personal(self, manager, mock_websocket):
        """Send personal should send to specific connection."""
        conn = await manager.connect(mock_websocket)

        result = await manager.send_personal(
            {"test": "data"},
            conn.connection_id
        )

        assert result is True
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["data"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_send_personal_nonexistent(self, manager):
        """Send personal should fail for unknown connection."""
        result = await manager.send_personal(
            {"test": "data"},
            "nonexistent"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager, mock_websocket_factory):
        """Send to user should send to all user connections."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        await manager.connect(ws1, user_id="user-123")
        await manager.connect(ws2, user_id="user-123")

        count = await manager.send_to_user(
            {"test": "data"},
            "user-123"
        )

        assert count == 2
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, manager, mock_websocket_factory):
        """Broadcast to room should send to all room members."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        conn1 = await manager.connect(ws1)
        conn2 = await manager.connect(ws2)

        await manager.join_room(conn1.connection_id, "test-room")
        await manager.join_room(conn2.connection_id, "test-room")

        count = await manager.broadcast_to_room(
            {"test": "data"},
            "test-room"
        )

        assert count == 2

    @pytest.mark.asyncio
    async def test_broadcast_to_room_with_exclude(
        self, manager, mock_websocket_factory
    ):
        """Broadcast should exclude specified connections."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        conn1 = await manager.connect(ws1)
        conn2 = await manager.connect(ws2)

        await manager.join_room(conn1.connection_id, "test-room")
        await manager.join_room(conn2.connection_id, "test-room")

        count = await manager.broadcast_to_room(
            {"test": "data"},
            "test-room",
            exclude={conn1.connection_id}
        )

        assert count == 1
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_all(self, manager, mock_websocket_factory):
        """Broadcast should send to all connections."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        await manager.connect(ws1)
        await manager.connect(ws2)

        count = await manager.broadcast({"test": "data"})

        assert count == 2

    @pytest.mark.asyncio
    async def test_broadcast_with_exclude(
        self, manager, mock_websocket_factory
    ):
        """Broadcast should respect exclusions."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        conn1 = await manager.connect(ws1)
        await manager.connect(ws2)

        count = await manager.broadcast(
            {"test": "data"},
            exclude={conn1.connection_id}
        )

        assert count == 1

    @pytest.mark.asyncio
    async def test_send_error(self, manager, mock_websocket):
        """Send error should send error message."""
        conn = await manager.connect(mock_websocket)

        result = await manager.send_error(
            conn.connection_id,
            "TEST_ERROR",
            "Test error message"
        )

        assert result is True
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.ERROR.value
        assert call_args["data"]["code"] == "TEST_ERROR"


# =============================================================================
# CONNECTION MANAGER - HEARTBEAT TESTS
# =============================================================================

class TestConnectionManagerHeartbeat:
    """Tests for heartbeat/ping-pong functionality."""

    @pytest.mark.asyncio
    async def test_handle_ping(self, manager, mock_websocket):
        """Handle ping should update last_ping and send pong."""
        conn = await manager.connect(mock_websocket)
        original_ping = conn.last_ping

        # Small delay to ensure time difference
        await asyncio.sleep(0.01)

        result = await manager.handle_ping(conn.connection_id)

        assert result is True
        assert conn.last_ping > original_ping
        # Verify pong was sent
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.PONG.value

    @pytest.mark.asyncio
    async def test_handle_ping_nonexistent(self, manager):
        """Handle ping should fail for unknown connection."""
        result = await manager.handle_ping("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_heartbeat_valid(self, manager, mock_websocket):
        """Check heartbeat should return True for active connection."""
        conn = await manager.connect(mock_websocket)

        result = await manager.check_heartbeat(conn.connection_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_heartbeat_timeout(self, manager, mock_websocket):
        """Check heartbeat should return False for timed out connection."""
        manager._heartbeat_timeout = 0.01
        conn = await manager.connect(mock_websocket)

        # Wait for timeout
        await asyncio.sleep(0.02)

        result = await manager.check_heartbeat(conn.connection_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_stale_connections(
        self, manager, mock_websocket_factory
    ):
        """Cleanup should remove stale connections."""
        manager._heartbeat_timeout = 0.01

        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        conn1 = await manager.connect(ws1)
        await asyncio.sleep(0.02)
        conn2 = await manager.connect(ws2)

        stale = await manager.cleanup_stale_connections()

        assert conn1.connection_id in stale
        assert conn2.connection_id not in stale
        assert manager.connection_count == 1


# =============================================================================
# CONNECTION MANAGER - METADATA TESTS
# =============================================================================

class TestConnectionManagerMetadata:
    """Tests for connection metadata management."""

    @pytest.mark.asyncio
    async def test_update_metadata_merge(self, manager, mock_websocket):
        """Update metadata should merge by default."""
        conn = await manager.connect(
            mock_websocket,
            metadata={"key1": "value1"}
        )

        result = manager.update_metadata(
            conn.connection_id,
            {"key2": "value2"}
        )

        assert result is True
        assert conn.metadata["key1"] == "value1"
        assert conn.metadata["key2"] == "value2"

    @pytest.mark.asyncio
    async def test_update_metadata_replace(self, manager, mock_websocket):
        """Update metadata can replace all."""
        conn = await manager.connect(
            mock_websocket,
            metadata={"key1": "value1"}
        )

        result = manager.update_metadata(
            conn.connection_id,
            {"key2": "value2"},
            merge=False
        )

        assert result is True
        assert "key1" not in conn.metadata
        assert conn.metadata["key2"] == "value2"

    def test_update_metadata_nonexistent(self, manager):
        """Update metadata should fail for unknown connection."""
        result = manager.update_metadata(
            "nonexistent",
            {"key": "value"}
        )

        assert result is False


# =============================================================================
# CONNECTION MANAGER - STATISTICS TESTS
# =============================================================================

class TestConnectionManagerStats:
    """Tests for statistics and monitoring."""

    @pytest.mark.asyncio
    async def test_get_stats(self, manager, mock_websocket_factory):
        """Get stats should return accurate statistics."""
        ws1 = mock_websocket_factory()
        ws2 = mock_websocket_factory()

        conn1 = await manager.connect(ws1, user_id="user1")
        conn2 = await manager.connect(ws2, user_id="user2")

        await manager.join_room(conn1.connection_id, "room1")
        await manager.join_room(conn2.connection_id, "room1")
        await manager.join_room(conn2.connection_id, "room2")

        stats = manager.get_stats()

        assert stats["total_connections"] == 2
        assert stats["total_rooms"] == 2
        assert stats["total_users"] == 2
        assert stats["rooms"]["room1"] == 2
        assert stats["rooms"]["room2"] == 1

    def test_get_room_list(self, manager):
        """Get room list should return empty for no rooms."""
        rooms = manager.get_room_list()

        assert rooms == []

    @pytest.mark.asyncio
    async def test_get_room_list_with_rooms(
        self, manager, mock_websocket
    ):
        """Get room list should return all rooms."""
        conn = await manager.connect(mock_websocket)
        await manager.join_room(conn.connection_id, "room1")
        await manager.join_room(conn.connection_id, "room2")

        rooms = manager.get_room_list()

        assert len(rooms) == 2
        assert "room1" in rooms
        assert "room2" in rooms


# =============================================================================
# MESSAGE TYPE ENUM TESTS
# =============================================================================

class TestMessageType:
    """Tests for MessageType enum."""

    def test_message_type_values(self):
        """Message types should have expected values."""
        assert MessageType.PING.value == "ping"
        assert MessageType.PONG.value == "pong"
        assert MessageType.MESSAGE.value == "message"
        assert MessageType.BROADCAST.value == "broadcast"
        assert MessageType.ROOM_JOIN.value == "room_join"
        assert MessageType.ROOM_LEAVE.value == "room_leave"
        assert MessageType.ROOM_MESSAGE.value == "room_message"
        assert MessageType.ERROR.value == "error"
        assert MessageType.SYSTEM.value == "system"
        assert MessageType.USER_JOINED.value == "user_joined"
        assert MessageType.USER_LEFT.value == "user_left"


# =============================================================================
# CONNECTION STATE ENUM TESTS
# =============================================================================

class TestConnectionState:
    """Tests for ConnectionState enum."""

    def test_connection_state_values(self):
        """Connection states should have expected values."""
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.DISCONNECTING.value == "disconnecting"
        assert ConnectionState.DISCONNECTED.value == "disconnected"


# =============================================================================
# SINGLETON INSTANCE TESTS
# =============================================================================

class TestSingletonInstance:
    """Tests for the global connection_manager singleton."""

    def test_singleton_exists(self):
        """Global connection_manager should exist."""
        assert connection_manager is not None
        assert isinstance(connection_manager, ConnectionManager)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_send_to_disconnected_fails(
        self, manager, mock_websocket
    ):
        """Sending to disconnected connection should fail gracefully."""
        conn = await manager.connect(mock_websocket)
        conn.state = ConnectionState.DISCONNECTED

        result = await manager.send_personal(
            {"test": "data"},
            conn.connection_id
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_websocket_send_exception(self, manager, mock_websocket):
        """Send should handle websocket exceptions gracefully."""
        conn = await manager.connect(mock_websocket)
        mock_websocket.send_json.side_effect = Exception("Network error")

        result = await manager.send_personal(
            {"test": "data"},
            conn.connection_id
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_room(self, manager):
        """Broadcast to nonexistent room should return 0."""
        count = await manager.broadcast_to_room(
            {"test": "data"},
            "nonexistent-room"
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_leave_nonexistent_room(self, manager, mock_websocket):
        """Leaving nonexistent room should return False."""
        conn = await manager.connect(mock_websocket)

        result = await manager.leave_room(
            conn.connection_id,
            "nonexistent-room"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_rooms_nonexistent(self, manager):
        """Get user rooms for unknown connection should return empty."""
        rooms = manager.get_user_rooms("nonexistent")

        assert len(rooms) == 0

    @pytest.mark.asyncio
    async def test_check_heartbeat_nonexistent(self, manager):
        """Check heartbeat for unknown connection should return False."""
        result = await manager.check_heartbeat("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_user_no_connections(self, manager):
        """Send to user with no connections should return 0."""
        count = await manager.send_to_user({"test": "data"}, "nonexistent-user")

        assert count == 0


# =============================================================================
# CONCURRENT OPERATIONS TESTS
# =============================================================================

class TestConcurrentOperations:
    """Tests for concurrent operation safety."""

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, manager, mock_websocket_factory):
        """Multiple concurrent connections should be handled."""
        tasks = [
            manager.connect(mock_websocket_factory())
            for _ in range(10)
        ]

        connections = await asyncio.gather(*tasks)

        assert manager.connection_count == 10
        assert len(set(c.connection_id for c in connections)) == 10

    @pytest.mark.asyncio
    async def test_concurrent_room_joins(self, manager, mock_websocket):
        """Concurrent room joins should be handled."""
        conn = await manager.connect(mock_websocket)

        tasks = [
            manager.join_room(conn.connection_id, f"room-{i}")
            for i in range(10)
        ]

        await asyncio.gather(*tasks)

        assert len(conn.rooms) == 10

    @pytest.mark.asyncio
    async def test_concurrent_broadcasts(
        self, manager, mock_websocket_factory
    ):
        """Concurrent broadcasts should be handled."""
        # Connect multiple clients
        for _ in range(5):
            await manager.connect(mock_websocket_factory())

        # Concurrent broadcasts
        tasks = [
            manager.broadcast({"msg": i})
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # Each broadcast should reach all 5 clients
        assert all(count == 5 for count in results)


# =============================================================================
# WEBSOCKET ROUTE INTEGRATION TESTS (using TestClient workarounds)
# =============================================================================

class TestWebSocketRouteHelpers:
    """Tests for WebSocket route helper functions."""

    def test_websocket_stats_endpoint_exists(self, client):
        """WebSocket stats endpoint should exist."""
        response = client.get("/ws/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_connections" in data
        assert "total_rooms" in data

    def test_websocket_rooms_list_endpoint(self, client):
        """WebSocket rooms list endpoint should exist."""
        response = client.get("/ws/rooms")
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data

    def test_websocket_room_info_not_found(self, client):
        """Room info should return 404 for unknown room."""
        response = client.get("/ws/rooms/nonexistent-room")
        assert response.status_code == 404
