from typing import Optional, Dict, List
import os
from datetime import datetime

# Try to import supabase, but don't fail if not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


class Database:
    """
    Database class with graceful fallback for local development.
    When Supabase is not configured, operations return empty data instead of failing.
    """

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.client = None

        # Only initialize if we have valid Supabase credentials (JWT tokens start with 'eyJ')
        if SUPABASE_AVAILABLE and self.url and self.key and self.key.startswith('eyJ'):  # pragma: no cover
            try:
                self.client = create_client(self.url, self.key)
                print("[OK] Supabase connected successfully")
            except Exception as e:
                print(f"Warning: Could not connect to Supabase: {e}")
                self.client = None
        else:
            print("[INFO] Running in local mode (no database persistence)")

    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.client is not None

    async def create_creator(self, email: str, name: str) -> Optional[Dict]:
        if not self.client:
            # Return mock data for local development
            return {
                "id": "local-creator",
                "email": email,
                "name": name,
                "credits_remaining": 100,
                "created_at": datetime.utcnow().isoformat()
            }

        # Supabase integration - requires real connection  # pragma: no cover
        response = self.client.table("creators").insert({
            "email": email,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        return response.data[0] if response.data else None

    async def get_creator(self, creator_id: str) -> Optional[Dict]:
        if not self.client:
            # Return mock creator for local development
            return {
                "id": creator_id,
                "email": "demo@example.com",
                "name": "Demo Creator",
                "credits_remaining": 100,
                "created_at": datetime.utcnow().isoformat()
            }

        # Supabase integration - requires real connection  # pragma: no cover
        response = self.client.table("creators").select("*").eq("id", creator_id).execute()
        return response.data[0] if response.data else None

    async def save_conversation(
        self,
        creator_id: str,
        student_message: str,
        ai_response: str,
        sources: List[str],
        should_escalate: bool = False
    ) -> Optional[Dict]:
        if not self.client:
            # Return mock data - conversation won't be persisted in local mode
            return {
                "id": f"local-{datetime.utcnow().timestamp()}",
                "creator_id": creator_id,
                "student_message": student_message,
                "ai_response": ai_response,
                "sources": sources,
                "should_escalate": should_escalate,
                "created_at": datetime.utcnow().isoformat()
            }

        # Supabase integration - requires real connection  # pragma: no cover
        response = self.client.table("conversations").insert({
            "creator_id": creator_id,
            "student_message": student_message,
            "ai_response": ai_response,
            "sources": sources,
            "should_escalate": should_escalate,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        return response.data[0] if response.data else None

    async def get_conversations(self, creator_id: str, limit: int = 50) -> List[Dict]:
        if not self.client:
            # Return empty list for local development (no persistence)
            return []

        # Supabase integration - requires real connection  # pragma: no cover
        response = self.client.table("conversations") \
            .select("*") \
            .eq("creator_id", creator_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []

    async def update_credit_usage(self, creator_id: str, credits_used: int) -> Optional[Dict]:
        if not self.client:
            # Return mock data for local development
            return {
                "id": creator_id,
                "credits_remaining": 100 - credits_used
            }

        # Supabase integration - requires real connection  # pragma: no cover
        creator = await self.get_creator(creator_id)
        if not creator:
            return None

        current_credits = creator.get("credits_remaining", 100)
        new_credits = max(0, current_credits - credits_used)

        response = self.client.table("creators") \
            .update({"credits_remaining": new_credits}) \
            .eq("id", creator_id) \
            .execute()

        return response.data[0] if response.data else None
