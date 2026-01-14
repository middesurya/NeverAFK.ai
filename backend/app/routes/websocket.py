"""
PRD-021: WebSocket Real-time Updates - WebSocket Endpoint

Provides WebSocket endpoints for real-time communication:
- WS /ws - Main WebSocket endpoint
- WS /ws/{connection_id} - Reconnection endpoint

Features:
- Connection handling with optional authentication
- Room join/leave operations
- Message broadcasting
- Ping/pong heartbeat
- Error handling

AC-1: WebSocket connection handling
AC-2: Message broadcasting support
AC-3: Room/channel management
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from typing import Optional
import json
import asyncio
from datetime import datetime

from app.services.connection_manager import (
    connection_manager,
    ConnectionManager,
    MessageType,
    ConnectionState
)
from app.utils.auth import get_optional_user_from_token, TokenData

router = APIRouter(tags=["WebSocket"])


async def get_user_from_websocket(
    token: Optional[str] = Query(None, alias="token")
) -> Optional[TokenData]:
    """
    Extract user from WebSocket query parameter token.

    Args:
        token: JWT token from query parameter

    Returns:
        TokenData if valid token, None otherwise
    """
    if not token:
        return None

    try:
        return await get_optional_user_from_token(token)
    except Exception:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    room: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint for real-time communication.

    Query Parameters:
        token: Optional JWT token for authentication
        room: Optional room to auto-join on connect

    Message Protocol:
        Incoming messages should be JSON with 'type' field:
        - ping: Heartbeat ping
        - message: Send message to server
        - room_join: Join a room (requires 'room' field)
        - room_leave: Leave a room (requires 'room' field)
        - room_message: Send message to room (requires 'room' and 'data' fields)
        - broadcast: Broadcast to all (admin only)

        Server responds with JSON containing:
        - type: Message type
        - data: Message payload
        - timestamp: ISO timestamp
    """
    connection = None
    user = None

    try:
        # Authenticate if token provided
        if token:
            user = await get_user_from_websocket(token)

        # Accept connection
        user_id = user.user_id if user else None
        connection = await connection_manager.connect(
            websocket=websocket,
            user_id=user_id,
            metadata={"authenticated": user is not None}
        )

        # Auto-join room if specified
        if room:
            await connection_manager.join_room(connection.connection_id, room)

        # Send connection confirmation
        await connection_manager.send_personal(
            {
                "connection_id": connection.connection_id,
                "user_id": user_id,
                "authenticated": user is not None,
                "rooms": list(connection.rooms)
            },
            connection.connection_id,
            MessageType.SYSTEM
        )

        # Message loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type", "message")

                # Handle different message types
                if msg_type == MessageType.PING.value:
                    await connection_manager.handle_ping(connection.connection_id)

                elif msg_type == MessageType.ROOM_JOIN.value:
                    target_room = message.get("room")
                    if target_room:
                        success = await connection_manager.join_room(
                            connection.connection_id, target_room
                        )
                        await connection_manager.send_personal(
                            {
                                "room": target_room,
                                "success": success,
                                "rooms": list(connection.rooms)
                            },
                            connection.connection_id,
                            MessageType.ROOM_JOIN
                        )
                    else:
                        await connection_manager.send_error(
                            connection.connection_id,
                            "MISSING_ROOM",
                            "Room name required for room_join"
                        )

                elif msg_type == MessageType.ROOM_LEAVE.value:
                    target_room = message.get("room")
                    if target_room:
                        success = await connection_manager.leave_room(
                            connection.connection_id, target_room
                        )
                        await connection_manager.send_personal(
                            {
                                "room": target_room,
                                "success": success,
                                "rooms": list(connection.rooms)
                            },
                            connection.connection_id,
                            MessageType.ROOM_LEAVE
                        )
                    else:
                        await connection_manager.send_error(
                            connection.connection_id,
                            "MISSING_ROOM",
                            "Room name required for room_leave"
                        )

                elif msg_type == MessageType.ROOM_MESSAGE.value:
                    target_room = message.get("room")
                    msg_data = message.get("data", {})
                    if target_room and target_room in connection.rooms:
                        await connection_manager.broadcast_to_room(
                            {
                                "from": connection.connection_id,
                                "user_id": connection.user_id,
                                "data": msg_data
                            },
                            target_room
                        )
                    elif target_room:
                        await connection_manager.send_error(
                            connection.connection_id,
                            "NOT_IN_ROOM",
                            f"You must join room '{target_room}' before sending messages"
                        )
                    else:
                        await connection_manager.send_error(
                            connection.connection_id,
                            "MISSING_ROOM",
                            "Room name required for room_message"
                        )

                elif msg_type == MessageType.MESSAGE.value:
                    # Echo back the message (for now)
                    await connection_manager.send_personal(
                        {
                            "echo": True,
                            "original": message.get("data", {})
                        },
                        connection.connection_id,
                        MessageType.MESSAGE
                    )

                else:
                    await connection_manager.send_error(
                        connection.connection_id,
                        "UNKNOWN_TYPE",
                        f"Unknown message type: {msg_type}"
                    )

            except json.JSONDecodeError:
                await connection_manager.send_error(
                    connection.connection_id,
                    "INVALID_JSON",
                    "Message must be valid JSON"
                )

    except WebSocketDisconnect:
        pass
    except ValueError as e:
        # Connection limit exceeded
        await websocket.close(code=1008, reason=str(e))
    except Exception as e:
        if connection:
            await connection_manager.send_error(
                connection.connection_id,
                "INTERNAL_ERROR",
                "An internal error occurred"
            )
    finally:
        if connection:
            await connection_manager.disconnect(connection.connection_id)


@router.websocket("/ws/{connection_id}")
async def websocket_reconnect(
    websocket: WebSocket,
    connection_id: str,
    token: Optional[str] = Query(None)
):
    """
    Reconnection endpoint for existing connection IDs.

    This allows clients to reconnect with a known connection ID,
    useful for recovering from brief disconnections.

    Path Parameters:
        connection_id: Previous connection ID to reuse

    Query Parameters:
        token: Optional JWT token for authentication
    """
    connection = None

    try:
        # Check if connection ID already exists
        existing = connection_manager.get_connection(connection_id)
        if existing:
            # Connection ID already in use, generate new one
            await websocket.close(
                code=1008,
                reason="Connection ID already in use"
            )
            return

        # Authenticate if token provided
        user = None
        if token:
            user = await get_user_from_websocket(token)

        user_id = user.user_id if user else None
        connection = await connection_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            metadata={"reconnected": True, "authenticated": user is not None}
        )

        # Send connection confirmation
        await connection_manager.send_personal(
            {
                "connection_id": connection.connection_id,
                "user_id": user_id,
                "authenticated": user is not None,
                "reconnected": True
            },
            connection.connection_id,
            MessageType.SYSTEM
        )

        # Same message loop as main endpoint
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type", "message")

                if msg_type == MessageType.PING.value:
                    await connection_manager.handle_ping(connection.connection_id)

                elif msg_type == MessageType.ROOM_JOIN.value:
                    target_room = message.get("room")
                    if target_room:
                        await connection_manager.join_room(
                            connection.connection_id, target_room
                        )

                elif msg_type == MessageType.ROOM_LEAVE.value:
                    target_room = message.get("room")
                    if target_room:
                        await connection_manager.leave_room(
                            connection.connection_id, target_room
                        )

                elif msg_type == MessageType.ROOM_MESSAGE.value:
                    target_room = message.get("room")
                    if target_room and target_room in connection.rooms:
                        await connection_manager.broadcast_to_room(
                            {
                                "from": connection.connection_id,
                                "user_id": connection.user_id,
                                "data": message.get("data", {})
                            },
                            target_room
                        )

            except json.JSONDecodeError:
                await connection_manager.send_error(
                    connection.connection_id,
                    "INVALID_JSON",
                    "Message must be valid JSON"
                )

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if connection:
            await connection_manager.disconnect(connection.connection_id)


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        Statistics about current connections and rooms
    """
    return connection_manager.get_stats()


@router.get("/ws/rooms")
async def list_rooms():
    """
    List all active rooms.

    Returns:
        List of active room names with member counts
    """
    rooms = connection_manager.get_room_list()
    return {
        "rooms": [
            {
                "name": room,
                "member_count": len(connection_manager.get_room_members(room))
            }
            for room in rooms
        ]
    }


@router.get("/ws/rooms/{room}")
async def get_room_info(room: str):
    """
    Get information about a specific room.

    Path Parameters:
        room: Room name

    Returns:
        Room information including member count
    """
    members = connection_manager.get_room_members(room)
    if not members:
        raise HTTPException(status_code=404, detail="Room not found")

    return {
        "name": room,
        "member_count": len(members),
        "members": list(members)
    }
