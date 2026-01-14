# Project: Creator Support AI

RAG-powered customer support platform for course creators. Built with Next.js 15 frontend and FastAPI backend with LangGraph multi-agent system.

## Quick Commands

### Frontend (from `frontend/` directory)
- `npm run dev` - Development server (port 3000)
- `npm run build` - Production build
- `npm run lint` - ESLint check
- `npx tsc --noEmit` - TypeScript check

### Backend (from `backend/` directory)
- `python main.py` - Run development server (port 8000)
- `uvicorn main:app --reload --host 0.0.0.0 --port 8000` - Alternative dev server
- `python test_api.py` - Run API tests
- `pytest test_api.py -v` - Run tests with pytest

## Code Style

### Python (Backend)
- Type hints required for all function signatures
- Use async/await for I/O operations
- Pydantic models for request/response validation
- HTTPException for error handling with specific status codes
- Imports order: stdlib, third-party, local

### TypeScript (Frontend)
- Use TypeScript strict mode
- "use client" directive for client components
- Path aliases with `@/*` for src/ imports
- Interface definitions for all props
- Tailwind CSS with CSS variables for styling

## Testing Rules

- Tests FIRST, always (TDD)
- No mocks for code that doesn't exist
- Given-When-Then structure for acceptance criteria
- API tests in `backend/test_api.py`
- Frontend tests in `frontend/` using vitest (when added)

## Git Workflow

- Branch naming: `feat/PRD-XXX-description`
- Commit after each TDD phase (red, green, refactor)
- PR requires passing tests

## Important Files

- `docs/implementation-plan.md` - Master plan (add your phases here)
- `docs/prds/` - All PRD definitions
- `skills/skills.md` - Learned patterns
- `progress/progress.md` - Current status

## Architecture Overview

```
Frontend (Next.js 15)          Backend (FastAPI)
├── Landing page               ├── /chat - RAG chat endpoint
├── Dashboard                  ├── /upload/content - Ingestion
├── Chat demo                  ├── /conversations - History
├── Embed widget               └── Multi-agent LangGraph
    generator                      ├── Course Content Agent
                                   ├── Policy Agent
                                   ├── Progress Tracker
                                   └── Escalation Agent
```

## Key Services

- **Vector Store**: Pinecone index `strongmvp`, namespaced by creator_id
- **Embeddings**: OpenAI `text-embedding-3-large` (1024 dims)
- **LLM**: OpenAI GPT-4 via LangGraph
- **Auth**: Supabase Auth with JWT
- **Database**: Supabase PostgreSQL
- **Payments**: Lemon Squeezy (credit-based billing)

## Environment Variables

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key

### Backend (.env)
- `OPENAI_API_KEY` - OpenAI API key
- `PINECONE_API_KEY` - Pinecone API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - JWT secret for token validation

## Production URLs

- Frontend: https://never-afk-ai-lngm.vercel.app
- Backend API: https://neverafkai-production.up.railway.app
- Embed Widget: https://never-afk-ai-lngm.vercel.app/embed.js

## Things Claude Should Know

- Project is live in production (v1.1.0)
- Auth is fully integrated with Supabase
- Embed widget is standalone JavaScript
- Credit-based billing system is coded but needs payment testing
- Multi-language support not yet implemented
- Mobile app not built (web is responsive)

## Anti-Patterns to Avoid

- Don't add mock data to production code
- Don't skip error handling on API calls
- Don't hardcode API URLs (use environment variables)
- Don't create tests that pass without implementation
- Don't modify tests to make them pass

## TDD Workflow

This project uses TDD-first development with subagent orchestration:

1. **Red Phase**: Write failing tests first
2. **Green Phase**: Write minimal code to pass
3. **Refactor Phase**: Clean up while keeping tests green
4. **Validate**: Run all acceptance criteria
5. **Learn**: Update skills.md with patterns

See `.claude/commands/` for orchestrator commands.
