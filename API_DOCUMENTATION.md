# API Documentation - Creator Support AI

Complete API reference for integrating with Creator Support AI backend.

## Base URL

**Development:** `http://localhost:8000`
**Production:** `https://your-api-domain.com`

## Authentication

Currently, the API uses creator_id for identifying users. Future versions will include JWT-based authentication.

---

## Endpoints

### Health & Status

#### GET /health

Health check endpoint to verify the API is running.

**Response:**
```json
{
  "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

#### GET /

Root endpoint with API information.

**Response:**
```json
{
  "message": "Creator Support AI API",
  "status": "running"
}
```

---

### Content Management

#### POST /upload/content

Upload and process course content (PDF, video, or text file).

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (file, required): The content file to upload
- `creator_id` (string, required): Creator's unique identifier
- `content_type` (string, required): Type of content (`pdf`, `video`, or `text`)
- `title` (string, optional): Title or name for the content

**Response:**
```json
{
  "status": "success",
  "filename": "module-1.pdf",
  "creator_id": "creator-123",
  "content_type": "pdf",
  "document_count": 1,
  "chunks_created": 24,
  "namespace": "creator-123"
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/upload/content \
  -F "file=@/path/to/module-1.pdf" \
  -F "creator_id=creator-123" \
  -F "content_type=pdf" \
  -F "title=Module 1: Introduction"
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/upload/content"
files = {
    'file': open('module-1.pdf', 'rb')
}
data = {
    'creator_id': 'creator-123',
    'content_type': 'pdf',
    'title': 'Module 1: Introduction'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('creator_id', 'creator-123');
formData.append('content_type', 'pdf');
formData.append('title', 'Module 1: Introduction');

const response = await fetch('http://localhost:8000/upload/content', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data);
```

**Error Responses:**
- `400 Bad Request`: Missing required parameters
- `500 Internal Server Error`: Processing failed

---

### Chat & Q&A

#### POST /chat

Send a message and receive an AI-generated response based on uploaded content.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "message": "What did you cover in Module 3?",
  "creator_id": "creator-123",
  "conversation_id": "conv-456"  // optional
}
```

**Parameters:**
- `message` (string, required): The student's question
- `creator_id` (string, required): Creator's unique identifier
- `conversation_id` (string, optional): ID to continue an existing conversation

**Response:**
```json
{
  "response": "In Module 3, we covered advanced Python concepts including decorators, generators, and context managers. The module focused on writing more Pythonic code and understanding Python's internals.",
  "sources": [
    "Module 3: Advanced Python (Score: 0.92)",
    "Module 3 Exercises (Score: 0.87)"
  ],
  "should_escalate": false,
  "conversation_id": "conv-456"
}
```

**Response Fields:**
- `response` (string): The AI-generated answer
- `sources` (array): List of content sources used, with relevance scores
- `should_escalate` (boolean): Whether this response should be reviewed by human
- `conversation_id` (string): Conversation identifier for follow-up messages

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What did you cover in Module 3?",
    "creator_id": "creator-123"
  }'
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/chat"
payload = {
    "message": "What did you cover in Module 3?",
    "creator_id": "creator-123"
}

response = requests.post(url, json=payload)
print(response.json())
```

**Example (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'What did you cover in Module 3?',
    creator_id: 'creator-123'
  })
});

const data = await response.json();
console.log(data);
```

**Error Responses:**
- `400 Bad Request`: Missing required fields
- `500 Internal Server Error`: Chat processing failed

---

### Conversation History

#### GET /conversations/{creator_id}

Retrieve conversation history for a creator.

**Parameters:**
- `creator_id` (path, required): Creator's unique identifier
- `limit` (query, optional): Maximum number of conversations to return (default: 50)

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv-789",
      "student_message": "How do I access the bonus materials?",
      "ai_response": "You can access the bonus materials in the Resources section of your dashboard...",
      "sources": ["FAQ Document (Score: 0.95)"],
      "should_escalate": false,
      "reviewed": false,
      "created_at": "2026-01-02T10:30:00Z"
    },
    {
      "id": "conv-788",
      "student_message": "What did you cover in Module 3?",
      "ai_response": "In Module 3, we covered...",
      "sources": ["Module 3: Advanced Topics (Score: 0.92)"],
      "should_escalate": false,
      "reviewed": true,
      "created_at": "2026-01-02T09:15:00Z"
    }
  ]
}
```

**Example (cURL):**
```bash
curl http://localhost:8000/conversations/creator-123?limit=10
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/conversations/creator-123"
params = {'limit': 10}

response = requests.get(url, params=params)
print(response.json())
```

**Example (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/conversations/creator-123?limit=10');
const data = await response.json();
console.log(data.conversations);
```

---

## Data Models

### ChatMessage (Request)

```typescript
interface ChatMessage {
  message: string;           // The question/message
  creator_id: string;        // Creator identifier
  conversation_id?: string;  // Optional conversation ID
}
```

### ChatResponse

```typescript
interface ChatResponse {
  response: string;          // AI-generated answer
  sources: string[];         // Source citations
  should_escalate: boolean;  // Whether to flag for review
  conversation_id: string;   // Conversation identifier
}
```

### Conversation

```typescript
interface Conversation {
  id: string;               // Unique conversation ID
  student_message: string;  // Original question
  ai_response: string;      // AI-generated response
  sources: string[];        // Source documents used
  should_escalate: boolean; // Escalation flag
  reviewed: boolean;        // Whether creator reviewed it
  created_at: string;       // ISO 8601 timestamp
}
```

---

## Rate Limiting

**Current:** No rate limiting implemented

**Planned:**
- Free tier: 100 requests/month
- Starter: 1,000 requests/month
- Pro: Unlimited

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters or missing required fields
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

---

## CORS

The API supports CORS for the following origins:
- Development: `http://localhost:3000`
- Production: Configure via `CORS_ORIGINS` environment variable

---

## Interactive API Documentation

Once the backend is running, visit:

**Swagger UI:** `http://localhost:8000/docs`

**ReDoc:** `http://localhost:8000/redoc`

These provide interactive API documentation where you can test endpoints directly.

---

## Webhooks (Future)

Planned webhook support for:
- New conversation created
- Response flagged for review
- Content processing completed

---

## SDK Examples

### Python SDK (Unofficial)

```python
class CreatorSupportAI:
    def __init__(self, api_url, creator_id):
        self.api_url = api_url
        self.creator_id = creator_id

    def upload_content(self, file_path, content_type, title=None):
        url = f"{self.api_url}/upload/content"
        files = {'file': open(file_path, 'rb')}
        data = {
            'creator_id': self.creator_id,
            'content_type': content_type,
            'title': title or os.path.basename(file_path)
        }
        response = requests.post(url, files=files, data=data)
        return response.json()

    def chat(self, message, conversation_id=None):
        url = f"{self.api_url}/chat"
        payload = {
            'message': message,
            'creator_id': self.creator_id,
            'conversation_id': conversation_id
        }
        response = requests.post(url, json=payload)
        return response.json()

    def get_conversations(self, limit=50):
        url = f"{self.api_url}/conversations/{self.creator_id}"
        response = requests.get(url, params={'limit': limit})
        return response.json()

# Usage
ai = CreatorSupportAI('http://localhost:8000', 'creator-123')

# Upload content
result = ai.upload_content('module-1.pdf', 'pdf', 'Module 1')

# Chat
response = ai.chat('What is covered in Module 1?')
print(response['response'])

# Get history
conversations = ai.get_conversations(limit=10)
```

### JavaScript SDK (Unofficial)

```javascript
class CreatorSupportAI {
  constructor(apiUrl, creatorId) {
    this.apiUrl = apiUrl;
    this.creatorId = creatorId;
  }

  async uploadContent(file, contentType, title) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('creator_id', this.creatorId);
    formData.append('content_type', contentType);
    if (title) formData.append('title', title);

    const response = await fetch(`${this.apiUrl}/upload/content`, {
      method: 'POST',
      body: formData
    });

    return await response.json();
  }

  async chat(message, conversationId = null) {
    const response = await fetch(`${this.apiUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        creator_id: this.creatorId,
        conversation_id: conversationId
      })
    });

    return await response.json();
  }

  async getConversations(limit = 50) {
    const response = await fetch(
      `${this.apiUrl}/conversations/${this.creatorId}?limit=${limit}`
    );

    return await response.json();
  }
}

// Usage
const ai = new CreatorSupportAI('http://localhost:8000', 'creator-123');

// Upload content
const result = await ai.uploadContent(fileInput.files[0], 'pdf', 'Module 1');

// Chat
const response = await ai.chat('What is covered in Module 1?');
console.log(response.response);

// Get history
const { conversations } = await ai.getConversations(10);
```

---

## Best Practices

### Content Upload
1. **Optimize file sizes**: Compress videos and PDFs before uploading
2. **Use descriptive titles**: Helps with source attribution
3. **Batch uploads**: Upload related content together
4. **Monitor processing**: Large files may take time to process

### Chat Queries
1. **Include conversation_id**: For multi-turn conversations
2. **Handle escalations**: Review flagged responses promptly
3. **Cache responses**: Reduce API calls for common questions
4. **Provide feedback**: Use review system to improve accuracy

### Performance
1. **Use pagination**: Limit conversation history requests
2. **Implement retry logic**: Handle transient failures
3. **Monitor rate limits**: Track usage against plan limits
4. **Cache embeddings**: Avoid re-processing same content

---

## Support

For API issues or questions:
- Check `/health` endpoint first
- Review error messages in response
- Check backend logs for details
- Verify environment variables are set

---

*Last Updated: 2026-01-02*
*API Version: 1.0.0*
