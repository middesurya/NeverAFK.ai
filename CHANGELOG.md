# Changelog

All notable changes to Creator Support AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-07

### 🔐 Authentication & Production Release

Full user authentication and production deployment!

### Added

#### Authentication System
- **Supabase Auth Integration**
  - Complete login/signup flow with email verification
  - Password reset functionality via email
  - Session management with automatic refresh
  - Protected routes requiring authentication
  - AuthContext provider for React

- **New Pages**
  - `/login` - User login with email/password
  - `/signup` - New user registration
  - `/auth/reset-password` - Password reset flow

#### Production Infrastructure
- **Deployed to Production**
  - Frontend on Vercel: https://never-afk-ai-lngm.vercel.app
  - Backend on Railway: https://neverafkai-production.up.railway.app
  - Embed widget working on external sites

### Changed

- **CORS Configuration**
  - Updated to allow all origins (`*`) for embed widget compatibility
  - Embed widget can now work on any external website

- **Embed Widget**
  - Fixed API URL to point to Railway production backend
  - Updated script source to Vercel production URL

- **Demo Page**
  - Now uses authenticated user's ID when logged in
  - Falls back to `demo-creator` for unauthenticated demo

- **Backend Auth**
  - Added JWT token verification middleware
  - Optional auth for chat/upload (supports both authenticated and demo mode)
  - User-specific content isolation

### Fixed

- Fixed embed widget CORS errors on external websites
- Fixed Railway API URL typo (removed hyphen)
- Fixed demo page showing wrong content for logged-in users

---

## [1.0.0] - 2026-01-02

### 🎉 Initial Release

The first production-ready version of Creator Support AI!

### Added

#### Core Features
- **RAG-Powered Chat System**
  - Multi-agent orchestration using LangGraph
  - Vector search with Pinecone
  - Source citations for all responses
  - Automatic escalation for uncertain answers
  - Conversation history tracking

- **Content Ingestion Pipeline**
  - PDF document processing with chunking
  - Video transcription using OpenAI Whisper
  - Text file processing
  - Automatic embedding generation
  - Support for multiple content types

- **Frontend Application**
  - Next.js 15 with TypeScript
  - Landing page with value proposition
  - Interactive chat demo interface
  - Creator dashboard with analytics
  - Content upload interface with drag-and-drop
  - Embed widget code generator
  - Pricing page with three tiers
  - Fully responsive design with Tailwind CSS

- **Backend API**
  - FastAPI with async support
  - RESTful endpoints for all operations
  - `/chat` - Send messages and get AI responses
  - `/upload/content` - Upload and process content
  - `/conversations/{creator_id}` - Retrieve chat history
  - `/health` - Health check endpoint
  - Comprehensive error handling
  - CORS support for cross-origin requests

- **Database & Storage**
  - PostgreSQL schema with Supabase
  - Row Level Security (RLS) policies
  - Vector storage in Pinecone
  - Conversation history persistence
  - User credit tracking system

- **Billing Integration**
  - Lemon Squeezy integration for payments
  - Credit-based billing system
  - Three pricing tiers (Free, Starter, Pro)
  - Usage tracking and limits

- **Documentation**
  - Comprehensive README with getting started guide
  - QUICKSTART guide for 15-minute setup
  - DEPLOYMENT guide for production deployment
  - API_DOCUMENTATION with all endpoints
  - LAUNCH_CHECKLIST for go-to-market
  - MARKETING_COPY with ready-to-use templates
  - DEMO_SCRIPT for video creation
  - TROUBLESHOOTING guide for common issues
  - CONTRIBUTING guide for developers
  - PROJECT_SUMMARY for complete overview

#### Developer Tools
- Environment validation script (`validate_env.py`)
- Sample data population script (`populate_sample_data.py`)
- API test suite (`test_api.py`)
- Docker support with Dockerfile and docker-compose
- Setup scripts for Windows (`.bat`) and Unix (`.sh`)

#### Embeddable Widget
- Standalone JavaScript widget (`embed.js`)
- Customizable appearance (colors, position)
- Mobile-responsive chat interface
- Easy one-line integration

### Technical Stack

**Backend:**
- Python 3.10+
- FastAPI 0.115.6
- LangGraph 0.2.63
- LangChain 0.3.14
- OpenAI API for LLM and embeddings
- Pinecone for vector search
- Supabase for PostgreSQL database

**Frontend:**
- Next.js 15
- React 19
- TypeScript 5
- Tailwind CSS 3.4
- Supabase client

### Infrastructure
- Vercel-ready for frontend deployment
- Railway/Render-ready for backend deployment
- Docker containerization support
- Environment-based configuration
- Health check endpoints

### Security
- Row Level Security (RLS) in database
- API key validation
- CORS configuration
- Input sanitization
- Secure environment variable handling

---

## [Unreleased]

### Planned for v1.1.0

#### Features
- [ ] Multi-language support (Spanish, French, German)
- [ ] Team collaboration features
- [ ] Advanced analytics dashboard
- [ ] Email notification system
- [ ] API rate limiting
- [ ] Webhook support

#### Improvements
- [ ] Response caching for common questions
- [ ] Improved chunking algorithm
- [ ] Better error messages
- [ ] Mobile app (React Native)
- [ ] Browser extension (Chrome/Firefox)

#### Bug Fixes
- [ ] TBD based on user feedback

---

## Version History

### Version Numbering

We use Semantic Versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Incompatible API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Schedule

- **Patch releases**: As needed for critical bugs
- **Minor releases**: Monthly with new features
- **Major releases**: Quarterly or when breaking changes needed

---

## Migration Guides

### Migrating to v1.0.0

This is the initial release, no migration needed.

---

## Deprecation Notices

None currently.

---

## Known Issues

### v1.0.0

1. **Video transcription limited to 25MB**
   - Workaround: Split large videos or extract audio first
   - Fix planned: Implement chunked upload in v1.1.0

2. **English language only**
   - Workaround: None
   - Fix planned: Multi-language support in v1.1.0

3. **Single creator per account**
   - Workaround: Create multiple accounts
   - Fix planned: Team features in v1.1.0

---

## Contributors

### v1.0.0

- Initial implementation and architecture
- Core RAG pipeline development
- Frontend and backend implementation
- Documentation and guides
- Testing and validation

---

## Acknowledgments

### Technologies Used

- **LangChain & LangGraph** - RAG and agent orchestration
- **OpenAI** - LLM and embeddings
- **Pinecone** - Vector database
- **Supabase** - PostgreSQL and authentication
- **Next.js** - React framework
- **FastAPI** - Python web framework
- **Tailwind CSS** - Styling
- **Lemon Squeezy** - Payment processing

### Inspiration

Built to solve the $60B support burden in the creator economy, helping course creators and digital product sellers scale their support without hiring.

---

## Support

For questions or issues:
- **Documentation**: Check the docs/ directory
- **Issues**: GitHub Issues
- **Email**: support@example.com
- **Community**: Discord (coming soon)

---

## License

[MIT License](LICENSE)

---

*Last Updated: 2026-01-02*
