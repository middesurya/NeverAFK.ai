# Contributing to Creator Support AI

Thank you for your interest in contributing! This guide will help you get started.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Making Changes](#making-changes)
6. [Testing](#testing)
7. [Code Style](#code-style)
8. [Submitting Changes](#submitting-changes)

---

## Code of Conduct

Be respectful, constructive, and professional. We welcome contributions from everyone.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git
- OpenAI API key
- Pinecone account

### Areas for Contribution

We welcome contributions in these areas:

**Features:**
- Multi-language support
- Voice/video responses
- Advanced analytics
- Mobile app
- Browser extensions

**Improvements:**
- Performance optimization
- Better error handling
- UI/UX enhancements
- Documentation updates
- Test coverage

**Bug Fixes:**
- Squash bugs in the issue tracker
- Fix edge cases
- Improve error messages

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR-USERNAME/strong_mvp.git
cd strong_mvp
```

### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Add your API keys to .env
# OPENAI_API_KEY=...
# PINECONE_API_KEY=...

# Validate environment
python validate_env.py --test-keys

# Run backend
python main.py
```

### 3. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 4. Verify Setup

```bash
# Backend should be running at http://localhost:8000
curl http://localhost:8000/health

# Frontend should be at http://localhost:3000
open http://localhost:3000
```

---

## Project Structure

```
strong_mvp/
├── backend/
│   ├── app/
│   │   ├── agents/           # LangGraph agents
│   │   ├── services/         # Business logic
│   │   └── models/           # Database models
│   ├── main.py               # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   └── components/       # React components
│   └── package.json
└── Documentation/
```

### Key Files

**Backend:**
- `main.py`: API endpoints
- `app/agents/support_agent.py`: LangGraph multi-agent system
- `app/services/vector_store.py`: Pinecone integration
- `app/services/content_ingestion.py`: File upload handling

**Frontend:**
- `src/app/page.tsx`: Landing page
- `src/components/ChatInterface.tsx`: Chat UI
- `src/app/dashboard/page.tsx`: Creator dashboard

---

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/`: New features
- `fix/`: Bug fixes
- `docs/`: Documentation updates
- `refactor/`: Code refactoring
- `test/`: Test additions/changes

### 2. Make Your Changes

Follow these guidelines:

**For Backend Changes:**
- Keep functions small and focused
- Add type hints to Python code
- Document complex logic
- Handle errors gracefully
- Update tests

**For Frontend Changes:**
- Use TypeScript
- Follow React best practices
- Keep components small
- Use Tailwind for styling
- Ensure mobile responsiveness

### 3. Common Development Tasks

**Add a New API Endpoint:**

```python
# backend/main.py

@app.get("/your-endpoint")
async def your_endpoint():
    """
    Description of what this endpoint does.

    Returns:
        dict: Response data
    """
    return {"message": "Hello!"}
```

**Add a New Frontend Page:**

```typescript
// frontend/src/app/your-page/page.tsx

export default function YourPage() {
  return (
    <main>
      <h1>Your Page</h1>
    </main>
  );
}
```

**Add a New Agent:**

```python
# backend/app/agents/your_agent.py

from langgraph.graph import StateGraph

class YourAgent:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(YourState)
        # Define nodes and edges
        return workflow.compile()
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test
pytest test_api.py::test_health_check

# Run with coverage
pytest --cov=app tests/
```

### Adding Tests

```python
# backend/tests/test_your_feature.py

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_your_feature():
    response = client.get("/your-endpoint")
    assert response.status_code == 200
    assert response.json()["message"] == "Expected"
```

### Frontend Tests

```bash
cd frontend

# Run tests (if configured)
npm test

# Type checking
npx tsc --noEmit

# Linting
npm run lint
```

### Manual Testing

```bash
# Populate sample data
cd backend
python populate_sample_data.py

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Python?", "creator_id": "demo-creator-123"}'
```

---

## Code Style

### Python (Backend)

Follow PEP 8 and use type hints:

```python
from typing import List, Dict, Optional

async def process_content(
    file_path: str,
    creator_id: str,
    metadata: Optional[Dict] = None
) -> Dict[str, int]:
    """
    Process uploaded content.

    Args:
        file_path: Path to the file
        creator_id: Creator's unique ID
        metadata: Optional metadata dict

    Returns:
        Dict with processing results
    """
    # Implementation
    return {"chunks": 10}
```

**Code Formatting:**

```bash
# Install formatters
pip install black isort

# Format code
black .
isort .

# Check style
flake8
```

### TypeScript/React (Frontend)

Use functional components and hooks:

```typescript
interface Props {
  title: string;
  onSubmit: (value: string) => void;
}

export default function MyComponent({ title, onSubmit }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    onSubmit(value);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">{title}</h2>
      {/* Component JSX */}
    </div>
  );
}
```

**Code Formatting:**

```bash
# Format code
npm run format  # If configured

# Or use Prettier
npx prettier --write "src/**/*.{ts,tsx}"
```

---

## Submitting Changes

### 1. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add multi-language support for chat responses"
```

**Commit Message Guidelines:**
- Use present tense ("Add feature" not "Added feature")
- Be specific and concise
- Reference issue numbers if applicable

Examples:
```
Add voice response feature (#123)
Fix CORS error in production deployment
Update API documentation for new endpoints
Refactor vector store for better performance
```

### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 3. Create a Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tested locally
- [ ] Added/updated tests
- [ ] All tests pass

## Screenshots (if applicable)

## Additional Notes
```

### 4. Code Review

- Respond to feedback promptly
- Make requested changes
- Push updates to the same branch
- Be open to suggestions

---

## Development Best Practices

### 1. Environment Management

```bash
# Always activate virtual environment
source venv/bin/activate

# Keep dependencies updated
pip install -r requirements.txt
npm install
```

### 2. Git Workflow

```bash
# Stay up to date with main branch
git checkout main
git pull upstream main

# Rebase your feature branch
git checkout feature/your-feature
git rebase main

# Resolve conflicts if any
# Test thoroughly
# Push changes
git push origin feature/your-feature --force-with-lease
```

### 3. Documentation

- Update README.md if you add features
- Document new API endpoints in API_DOCUMENTATION.md
- Add code comments for complex logic
- Update CHANGELOG.md

### 4. Performance

- Profile code changes
- Avoid N+1 queries
- Cache when appropriate
- Optimize bundle size
- Use async/await properly

---

## Reporting Issues

### Bug Reports

Include:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, Node version)
- Error messages and logs
- Screenshots if applicable

### Feature Requests

Include:
- Problem you're trying to solve
- Proposed solution
- Alternative solutions considered
- Additional context

---

## Community

- **Discussions:** GitHub Discussions
- **Chat:** Discord (if available)
- **Issues:** GitHub Issues
- **Email:** support@example.com

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Mentioned in project documentation

---

## Questions?

If you have questions:
1. Check existing documentation
2. Search GitHub Issues
3. Ask in Discussions
4. Email maintainers

---

Thank you for contributing to Creator Support AI! 🚀

*Your contributions help creators worldwide save time and serve their students better.*
