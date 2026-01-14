"""
Mock implementation for Supabase database service.
PRD-002: Mock External Services
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class MockDatabase:
    """Mock implementation of Database for testing without actual database calls."""

    def __init__(
        self,
        connected: bool = True,
        raise_exception: Optional[Exception] = None
    ):
        self._connected = connected
        self._raise_exception = raise_exception
        self._conversations: List[Dict[str, Any]] = []
        self._creators: Dict[str, Dict[str, Any]] = {}
        self.call_history: List[Dict[str, Any]] = []

    @property
    def call_count(self) -> int:
        return len(self.call_history)

    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected

    def set_creator_credits(self, creator_id: str, credits: int) -> None:
        """Set credits for a creator (test helper method)."""
        if creator_id not in self._creators:
            self._creators[creator_id] = {
                "id": creator_id,
                "email": f"{creator_id}@example.com",
                "name": f"Creator {creator_id}",
                "credits_remaining": credits,
                "created_at": datetime.now().isoformat()
            }
        else:
            self._creators[creator_id]["credits_remaining"] = credits

    async def save_conversation(
        self,
        creator_id: str,
        student_message: str,
        ai_response: str,
        sources: List[str],
        should_escalate: bool
    ) -> Dict[str, Any]:
        """Save a conversation to the mock database."""
        if self._raise_exception:
            raise self._raise_exception

        # Record the call
        self.call_history.append({
            "method": "save_conversation",
            "creator_id": creator_id,
            "student_message": student_message,
            "ai_response": ai_response,
            "sources": sources,
            "should_escalate": should_escalate,
            "timestamp": datetime.now()
        })

        conversation = {
            "id": str(uuid.uuid4()),
            "creator_id": creator_id,
            "student_message": student_message,
            "ai_response": ai_response,
            "sources": sources,
            "should_escalate": should_escalate,
            "created_at": datetime.now().isoformat()
        }

        self._conversations.append(conversation)
        return conversation

    async def get_conversations(
        self,
        creator_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversations for a creator."""
        if self._raise_exception:
            raise self._raise_exception

        # Record the call
        self.call_history.append({
            "method": "get_conversations",
            "creator_id": creator_id,
            "limit": limit,
            "timestamp": datetime.now()
        })

        # Filter by creator_id
        filtered = [c for c in self._conversations if c["creator_id"] == creator_id]
        return filtered[:limit]

    async def update_credit_usage(
        self,
        creator_id: str,
        credits_used: int
    ) -> Dict[str, Any]:
        """Update credit usage for a creator."""
        if self._raise_exception:
            raise self._raise_exception

        # Record the call
        self.call_history.append({
            "method": "update_credit_usage",
            "creator_id": creator_id,
            "credits_used": credits_used,
            "timestamp": datetime.now()
        })

        # Get or create creator
        if creator_id not in self._creators:
            self._creators[creator_id] = {
                "id": creator_id,
                "credits_remaining": 0
            }

        # Deduct credits, ensuring non-negative
        current = self._creators[creator_id]["credits_remaining"]
        new_credits = max(0, current - credits_used)
        self._creators[creator_id]["credits_remaining"] = new_credits

        return {"credits_remaining": new_credits}

    async def get_creator(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """Get creator by ID."""
        if self._raise_exception:
            raise self._raise_exception

        # Record the call
        self.call_history.append({
            "method": "get_creator",
            "creator_id": creator_id,
            "timestamp": datetime.now()
        })

        return self._creators.get(creator_id)

    async def create_creator(
        self,
        email: str,
        name: str
    ) -> Dict[str, Any]:
        """Create a new creator."""
        if self._raise_exception:
            raise self._raise_exception

        # Record the call
        self.call_history.append({
            "method": "create_creator",
            "email": email,
            "name": name,
            "timestamp": datetime.now()
        })

        creator_id = str(uuid.uuid4())
        creator = {
            "id": creator_id,
            "email": email,
            "name": name,
            "credits_remaining": 100,  # Default credits for new creators
            "created_at": datetime.now().isoformat()
        }

        self._creators[creator_id] = creator
        return creator

    def reset_history(self) -> None:
        """Reset call history and stored data."""
        self.call_history = []
        self._conversations = []
        self._creators = {}
