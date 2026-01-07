# Creator Support AI - RAG-Powered Customer Support

An AI-powered customer support system that understands your course content and answers student questions automatically using RAG (Retrieval-Augmented Generation).

## Live Demo

| Link | Description |
|------|-------------|
| [Live Demo](https://never-afk-ai-lngm.vercel.app/demo) | Try the AI chat |
| [Landing Page](https://never-afk-ai-lngm.vercel.app) | Product homepage |
| [API Health](https://neverafkai-production.up.railway.app/health) | Backend status |

## Features

- **Content-Aware AI**: Indexes course videos, PDFs, and text to answer specific content questions
- **Multi-Agent RAG Pipeline**: Uses LangGraph to orchestrate retrieval and response generation
- **Automatic Transcription**: Converts video content to searchable text using OpenAI Whisper
- **Embed Widget**: Easy-to-integrate chat widget for your course platform
- **Creator Dashboard**: Review conversations, manage content, and monitor performance
- **Credit-Based Billing**: Integrated with Lemon Squeezy for payments
- **Escalation System**: Flags uncertain responses for human review

## Tech Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Supabase Auth** - Authentication

### Backend
- **FastAPI** - Python web framework
- **LangGraph** - Multi-agent orchestration
- **LangChain** - RAG pipeline
- **OpenAI** - LLM (GPT-4) and embeddings
- **Pinecone** - Vector database
- **Supabase** - PostgreSQL database
- **Whisper API** - Video transcription

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- OpenAI API key
- Pinecone account
- Supabase project (optional but recommended)
- Lemon Squeezy account (for billing)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

5. Add your API keys to `.env`:
   ```
   OPENAI_API_KEY=your_key_here
   PINECONE_API_KEY=your_key_here
   SUPABASE_URL=your_url_here
   SUPABASE_ANON_KEY=your_key_here
   LEMON_SQUEEZY_API_KEY=your_key_here
   ```

6. Run the FastAPI server:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

### Database Setup

If using Supabase:

1. Create a new Supabase project
2. Run the SQL schema from `backend/schema.sql` in the Supabase SQL editor
3. Enable Row Level Security policies
4. Add your Supabase credentials to `.env`

## Project Structure

```
strong_mvp/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Landing page
│   │   │   ├── demo/              # Chat demo
│   │   │   ├── dashboard/         # Creator dashboard
│   │   │   └── pricing/           # Pricing page
│   │   └── components/
│   │       ├── ChatInterface.tsx  # Chat UI
│   │       ├── EmbedWidget.tsx    # Widget generator
│   │       └── ContentUpload.tsx  # File upload
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── support_agent.py   # LangGraph agent
│   │   ├── services/
│   │   │   ├── vector_store.py    # Pinecone integration
│   │   │   ├── document_processor.py
│   │   │   ├── content_ingestion.py
│   │   │   └── billing.py         # Lemon Squeezy
│   │   └── models/
│   │       └── database.py        # Supabase client
│   ├── main.py                    # FastAPI app
│   ├── requirements.txt
│   └── schema.sql                 # Database schema
└── README.md
```

## Usage

### Upload Content

1. Go to the dashboard at `/dashboard`
2. Navigate to the "Upload Content" section
3. Select content type (PDF, video, or text)
4. Upload your course materials
5. The system will automatically process and index the content

### Embed on Your Website

1. Go to the dashboard
2. Click on "Embed Widget"
3. Copy the JavaScript snippet
4. Paste it into your website's HTML

### Test the Chat

1. Visit `/demo` to test the chat interface
2. Ask questions about your uploaded content
3. The AI will respond with citations to specific sources

## API Endpoints

### POST /upload/content
Upload and process course content

**Body:**
- `file`: File upload (PDF, video, or text)
- `creator_id`: Creator's unique ID
- `content_type`: Type of content (pdf, video, text)
- `title`: Optional title

### POST /chat
Send a message to the AI assistant

**Body:**
```json
{
  "message": "What did you cover in Module 3?",
  "creator_id": "creator-id",
  "conversation_id": "optional-conversation-id"
}
```

**Response:**
```json
{
  "response": "In Module 3, we covered...",
  "sources": ["Module 3: Advanced Topics (Score: 0.92)"],
  "should_escalate": false,
  "conversation_id": "conv-123"
}
```

### GET /conversations/{creator_id}
Retrieve conversation history

**Query Parameters:**
- `limit`: Number of conversations (default: 50)

## Deployment

### Current Production Setup

| Component | Service | URL |
|-----------|---------|-----|
| Frontend | Vercel | https://never-afk-ai-lngm.vercel.app |
| Backend | Railway | https://neverafkai-production.up.railway.app |
| Database | Supabase | PostgreSQL (managed) |
| Vector Store | Pinecone | Cloud-hosted |

### Backend (FastAPI) - Railway

1. Create Railway project
2. Set root directory to `/backend`
3. Add environment variables:
   - `OPENAI_API_KEY`
   - `PINECONE_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
4. Deploy via GitHub integration

### Frontend (Next.js) - Vercel

1. Create Vercel project
2. Set root directory to `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = Railway backend URL
4. Deploy via GitHub integration

### Alternative Deployment Options

**Backend:**
- Render
- AWS Lambda (with Mangum)
- Google Cloud Run

**Frontend:**
- Netlify
- AWS Amplify

## Pricing Strategy

- **Free**: 100 responses/month
- **Starter ($29/mo)**: 1,000 responses/month
- **Pro ($49/mo)**: Unlimited responses

## Roadmap

- [ ] Multi-language support
- [ ] Voice responses using ElevenLabs
- [ ] Video avatar responses using HeyGen
- [ ] Advanced analytics dashboard
- [ ] A/B testing for responses
- [ ] Integration with Zapier
- [ ] Mobile app

## Contributing

This is a personal MVP project. Contributions and feedback are welcome!

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
