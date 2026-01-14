from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import os
import json
import uuid
from dotenv import load_dotenv
import tempfile
from pathlib import Path

from app.services.content_ingestion import ContentIngestionService
from app.services.vector_store import VectorStoreService
from app.agents.support_agent import SupportAgent
from app.models.database import Database
from app.utils.auth import get_current_user, get_optional_user, TokenData
from app.routes.websocket import router as websocket_router

load_dotenv()

app = FastAPI(title="Creator Support AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for embed widget to work on any website
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = VectorStoreService()
ingestion_service = ContentIngestionService()
support_agent = SupportAgent(vector_store)
db = Database()

# Include WebSocket router
app.include_router(websocket_router)


class ChatMessage(BaseModel):
    message: str
    creator_id: Optional[str] = None  # Optional - will use authenticated user's ID if not provided
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    should_escalate: bool
    conversation_id: str


@app.get("/")
async def root():
    return {"message": "Creator Support AI API", "status": "running"}


@app.post("/upload/content")
async def upload_content(
    file: UploadFile = File(...),
    creator_id: str = Form(None),
    content_type: str = Form(...),
    title: str = Form(None),
    user: Optional[TokenData] = Depends(get_optional_user)
):
    # Use authenticated user's ID if available, otherwise fall back to form data (for demo)
    effective_creator_id = user.user_id if user else creator_id

    if not effective_creator_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required or creator_id must be provided"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        metadata = {"title": title or file.filename}
        result = await ingestion_service.ingest_content(
            file_path=tmp_file_path,
            content_type=content_type,
            creator_id=effective_creator_id,
            metadata=metadata
        )

        return {
            "status": "success",
            "filename": file.filename,
            "creator_id": effective_creator_id,
            "content_type": content_type,
            **result
        }
    finally:
        os.unlink(tmp_file_path)


@app.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    user: Optional[TokenData] = Depends(get_optional_user)
):
    # Use authenticated user's ID if available, otherwise fall back to message data (for demo)
    effective_creator_id = user.user_id if user else message.creator_id

    if not effective_creator_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required or creator_id must be provided"
        )

    result = await support_agent.process_query(
        query=message.message,
        creator_id=effective_creator_id,
        conversation_history=[]
    )

    # Save conversation (works with or without database)
    await db.save_conversation(
        creator_id=effective_creator_id,
        student_message=message.message,
        ai_response=result["response"],
        sources=result["sources"],
        should_escalate=result["should_escalate"]
    )

    # Update credit usage
    await db.update_credit_usage(effective_creator_id, 1)

    return ChatResponse(
        response=result["response"],
        sources=result["sources"],
        should_escalate=result["should_escalate"],
        conversation_id=message.conversation_id or "new-conversation-id"
    )


async def stream_chat_generator(
    message_text: str,
    creator_id: str,
    conversation_id: Optional[str],
    database
) -> AsyncGenerator[str, None]:
    """
    Async generator for SSE streaming chat responses.
    Yields token events followed by a final done event with metadata.
    """
    # Get response from support agent
    result = await support_agent.process_query(
        query=message_text,
        creator_id=creator_id,
        conversation_history=[]
    )

    response_text = result["response"]
    sources = result["sources"]
    should_escalate = result["should_escalate"]

    # Generate or use provided conversation_id
    final_conversation_id = conversation_id or str(uuid.uuid4())

    # Stream tokens (split response into words/chunks)
    if response_text:
        # Split response into words and yield each as a token event
        words = response_text.split(" ")
        for i, word in enumerate(words):
            # Add space before word except for first word
            token_content = word if i == 0 else " " + word
            token_event = {"type": "token", "content": token_content}
            yield f"data: {json.dumps(token_event)}\n\n"

    # Yield final done event with metadata
    done_event = {
        "type": "done",
        "sources": sources,
        "should_escalate": should_escalate,
        "conversation_id": final_conversation_id
    }
    yield f"data: {json.dumps(done_event)}\n\n"

    # Save conversation to database after streaming completes
    await database.save_conversation(
        creator_id=creator_id,
        student_message=message_text,
        ai_response=response_text,
        sources=sources,
        should_escalate=should_escalate
    )

    # Update credit usage
    await database.update_credit_usage(creator_id, 1)


@app.post("/chat/stream")
async def chat_stream(
    message: ChatMessage,
    user: Optional[TokenData] = Depends(get_optional_user)
):
    """
    SSE streaming chat endpoint.
    Returns a stream of token events followed by a done event with metadata.
    """
    # Use authenticated user's ID if available, otherwise fall back to message data
    effective_creator_id = user.user_id if user else message.creator_id

    if not effective_creator_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required or creator_id must be provided"
        )

    return StreamingResponse(
        stream_chat_generator(
            message_text=message.message,
            creator_id=effective_creator_id,
            conversation_id=message.conversation_id,
            database=db
        ),
        media_type="text/event-stream; charset=utf-8"
    )


@app.get("/conversations/{creator_id}")
async def get_conversations(
    creator_id: str,
    limit: int = 50,
    user: Optional[TokenData] = Depends(get_optional_user)
):
    # Use authenticated user's ID if available
    effective_creator_id = user.user_id if user else creator_id

    # If authenticated, only allow access to own conversations
    if user and creator_id != user.user_id and creator_id != "demo-creator":
        raise HTTPException(
            status_code=403,
            detail="You can only access your own conversations"
        )

    conversations = await db.get_conversations(effective_creator_id, limit)
    return {"conversations": conversations}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected" if db.is_connected() else "local_mode",
        "mode": "production" if db.is_connected() else "development"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
