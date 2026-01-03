from supabase import create_client, Client
from typing import Optional, Dict, List
import os
from datetime import datetime


class Database:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.client: Client = create_client(self.url, self.key) if self.url and self.key else None

    async def create_creator(self, email: str, name: str) -> Dict:
        if not self.client:
            raise Exception("Supabase client not initialized")

        response = self.client.table("creators").insert({
            "email": email,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        return response.data[0] if response.data else None

    async def get_creator(self, creator_id: str) -> Optional[Dict]:
        if not self.client:
            raise Exception("Supabase client not initialized")

        response = self.client.table("creators").select("*").eq("id", creator_id).execute()
        return response.data[0] if response.data else None

    async def save_conversation(
        self,
        creator_id: str,
        student_message: str,
        ai_response: str,
        sources: List[str],
        should_escalate: bool = False
    ) -> Dict:
        if not self.client:
            raise Exception("Supabase client not initialized")

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
            raise Exception("Supabase client not initialized")

        response = self.client.table("conversations") \
            .select("*") \
            .eq("creator_id", creator_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []

    async def update_credit_usage(self, creator_id: str, credits_used: int) -> Dict:
        if not self.client:
            raise Exception("Supabase client not initialized")

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
