# Quick Start Guide - Creator Support AI

Get your RAG-powered support system running in 15 minutes.

## Prerequisites Check

Before starting, ensure you have:
- [ ] Node.js 18+ installed
- [ ] Python 3.10+ installed
- [ ] OpenAI API key
- [ ] Pinecone account (free tier works)

## Step-by-Step Setup

### 1. OpenAI API Key (2 minutes)

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key and save it

### 2. Pinecone Setup (3 minutes)

1. Sign up at https://www.pinecone.io/
2. Create a new index:
   - Name: `creator-support-ai`
   - Dimensions: `1536`
   - Metric: `cosine`
   - Cloud: `AWS`
   - Region: `us-east-1`
3. Copy your API key from the dashboard

### 3. Backend Setup (5 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `.env` and add your keys:
```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
```

Start the server:
```bash
python main.py
```

You should see: `Uvicorn running on http://0.0.0.0:8000`

### 4. Frontend Setup (3 minutes)

Open a new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

You should see: `Local: http://localhost:3000`

### 5. Test It (2 minutes)

1. Open http://localhost:3000 in your browser
2. Go to http://localhost:3000/demo
3. Try sending a message (won't have context yet)

## Upload Your First Content

1. Create a simple text file `test-content.txt`:
```
Module 1: Introduction

Welcome to the course! In this module, we cover:
- Getting started with the platform
- Setting up your workspace
- Understanding the basics

Key concepts:
- Always save your work frequently
- Use the help button if you get stuck
- Practice makes perfect
```

2. Use curl to upload (or use Postman):
```bash
curl -X POST http://localhost:8000/upload/content \
  -F "file=@test-content.txt" \
  -F "creator_id=demo-creator-id" \
  -F "content_type=text" \
  -F "title=Module 1: Introduction"
```

3. Go back to http://localhost:3000/demo
4. Ask: "What did you cover in Module 1?"
5. The AI should respond with the content!

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (must be 3.10+)
- Check if port 8000 is in use
- Verify API keys in `.env`

### Frontend won't start
- Check Node version: `node --version` (must be 18+)
- Delete `node_modules` and run `npm install` again
- Check if port 3000 is in use

### API errors
- Check backend console for error messages
- Verify Pinecone index exists and matches settings
- Verify OpenAI API key has credits

### No AI responses
- Check that you uploaded content first
- Verify the creator_id matches (`demo-creator-id`)
- Check backend logs for errors

## Next Steps

1. **Upload more content**: PDFs, videos, etc.
2. **Customize the UI**: Edit components in `frontend/src/components/`
3. **Set up Supabase**: For persistent storage and auth
4. **Configure billing**: Add Lemon Squeezy integration
5. **Deploy**: Use Vercel for frontend, Render for backend

## Development Tips

### Backend Hot Reload
```bash
uvicorn main:app --reload
```

### Frontend Dev Mode
Already has hot reload built-in with `npm run dev`

### Check API Health
```bash
curl http://localhost:8000/health
```

### View API Docs
Open http://localhost:8000/docs for interactive API documentation

## What You Built

You now have:
- ✅ RAG-powered chat system
- ✅ Content ingestion pipeline
- ✅ Vector search with Pinecone
- ✅ LangGraph multi-agent system
- ✅ React chat interface
- ✅ Creator dashboard
- ✅ Embed widget generator

## Ready to Launch?

Check out the full [README.md](README.md) for:
- Deployment guides
- Production configuration
- Security best practices
- Scaling tips
