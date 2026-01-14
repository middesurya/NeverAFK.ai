# AGENTS.md - AI Coding Agent Guidelines

This document provides guidelines for AI agents working on the Creator Support AI codebase, a RAG-powered customer support platform for course creators.

## Project Overview

Full-stack application with:
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS (in `frontend/`)
- **Backend**: FastAPI + LangGraph + LangChain + Pinecone (in `backend/`)
- **Database**: Supabase (PostgreSQL) + Pinecone (vector store)
- **Auth**: Supabase Auth with JWT tokens

## Build/Lint/Test Commands

### Frontend (from `frontend/` directory)

```bash
# Install dependencies
npm install

# Development server (port 3000)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint with ESLint
npm run lint

# Type check (no emit)
npx tsc --noEmit
```

### Backend (from `backend/` directory)

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (port 8000)
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run all API tests (requires server running on localhost:8000)
python test_api.py

# Run with Docker
docker-compose up
```

### Running Single Tests

The backend uses a custom test runner (`test_api.py`) with the `requests` library. To run individual tests:

```bash
# Modify test_api.py to call specific test functions, or use pytest:
pip install pytest
pytest test_api.py::test_health_check -v
pytest test_api.py -k "chat" -v
```

## Code Style Guidelines

### Python (Backend)

**Imports** - Order: standard library, third-party, local modules:
```python
import os
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from app.services.vector_store import VectorStoreService
from app.utils.auth import get_current_user
```

**Naming Conventions**:
- Functions/variables: `snake_case` (e.g., `get_current_user`, `creator_id`)
- Classes: `PascalCase` (e.g., `VectorStoreService`, `TokenData`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `BASE_URL`)

**Type Hints** - Always use type hints for function signatures:
```python
async def similarity_search(
    self,
    query: str,
    creator_id: str,
    k: int = 4,
    namespace: Optional[str] = None
) -> List[Document]:
```

**Async/Await** - Use async for I/O operations:
```python
async def process_query(self, query: str, creator_id: str) -> Dict:
    results = await self.vector_store.similarity_search(query, creator_id)
    return {"response": response, "sources": sources}
```

**Error Handling** - Use HTTPException with specific status codes:
```python
if not effective_creator_id:
    raise HTTPException(
        status_code=401,
        detail="Authentication required or creator_id must be provided"
    )
```

**Docstrings** - Use triple-quoted docstrings with Args/Returns:
```python
def verify_token(token: str) -> TokenData:
    """
    Verify and decode a Supabase JWT token.

    Args:
        token: The JWT token string to verify

    Returns:
        TokenData with user_id and email extracted from the token

    Raises:
        HTTPException: If token is invalid or expired
    """
```

**Pydantic Models** - Use for request/response validation:
```python
class ChatMessage(BaseModel):
    message: str
    creator_id: Optional[str] = None
    conversation_id: Optional[str] = None
```

### TypeScript/React (Frontend)

**Imports** - Order: React, Next.js, third-party, local:
```typescript
"use client";

import { useState, useRef, useEffect } from "react";
import type { Metadata } from "next";

import { AuthProvider } from "@/contexts/AuthContext";
import ChatInterface from "@/components/ChatInterface";
```

**Naming Conventions**:
- Functions/variables: `camelCase` (e.g., `sendMessage`, `isLoading`)
- Components/Interfaces: `PascalCase` (e.g., `ChatInterface`, `Message`)
- CSS variables: `--color-*` pattern (e.g., `--color-bg-primary`)

**Component Props** - Define interfaces for props:
```typescript
interface ChatInterfaceProps {
  creatorId: string;
  authToken?: string | null;
}

export default function ChatInterface({ creatorId, authToken }: ChatInterfaceProps) {
```

**Client Components** - Add "use client" directive at top:
```typescript
"use client";

import { useState } from "react";
```

**Path Aliases** - Use `@/*` for imports from `src/`:
```typescript
import { AuthProvider } from "@/contexts/AuthContext";
```

**Error Handling** - Try/catch with console.error:
```typescript
try {
  const response = await fetch(`${apiUrl}/chat`, { ... });
  const data = await response.json();
} catch (error) {
  console.error("Error sending message:", error);
}
```

**Styling** - Use Tailwind classes with CSS variables:
```typescript
<div className="bg-[var(--color-bg-primary)] text-[var(--color-text-primary)]">
```

## Project Structure

```
strong_mvp/
├── frontend/                    # Next.js 15 application
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   ├── components/         # React components
│   │   ├── contexts/           # React contexts (AuthContext)
│   │   └── lib/                # Utilities (supabase.ts)
│   ├── public/                 # Static assets + embed.js
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── agents/            # LangGraph agents (support_agent.py)
│   │   ├── services/          # Business logic (vector_store, ingestion)
│   │   ├── models/            # Database models
│   │   └── utils/             # Utilities (auth.py)
│   ├── main.py                # FastAPI entry point
│   ├── requirements.txt
│   └── test_api.py            # API tests
│
└── docker-compose.yml
```

## Environment Variables

**Frontend** (`.env.local`):
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key

**Backend** (`.env`):
- `OPENAI_API_KEY` - OpenAI API key
- `PINECONE_API_KEY` - Pinecone API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - JWT secret for token validation

## Key Patterns

### API Endpoints
All backend endpoints are in `backend/main.py`. Key routes:
- `POST /chat` - Chat with AI (uses RAG pipeline)
- `POST /upload/content` - Upload content for indexing
- `GET /conversations/{creator_id}` - Get conversation history
- `GET /health` - Health check

### Authentication
- Uses Supabase Auth with JWT tokens
- `get_current_user` dependency for protected routes
- `get_optional_user` for routes that work with/without auth

### Vector Store
- Pinecone index: `strongmvp`
- Embeddings: OpenAI `text-embedding-3-large` (1024 dimensions)
- Namespaces: One per creator_id

## Common Tasks

**Adding a new API endpoint**:
1. Add route in `backend/main.py`
2. Create Pydantic models for request/response
3. Add tests in `test_api.py`

**Adding a new frontend page**:
1. Create directory in `frontend/src/app/`
2. Add `page.tsx` with component
3. Use "use client" if client-side features needed

**Adding a new service**:
1. Create file in `backend/app/services/`
2. Use class-based pattern with async methods
3. Import and instantiate in `main.py`
