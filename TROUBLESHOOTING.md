# Troubleshooting Guide - Creator Support AI

Common issues and solutions for Creator Support AI.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Backend Issues](#backend-issues)
3. [Frontend Issues](#frontend-issues)
4. [API Issues](#api-issues)
5. [Content Upload Issues](#content-upload-issues)
6. [Chat Response Issues](#chat-response-issues)
7. [Deployment Issues](#deployment-issues)
8. [Performance Issues](#performance-issues)

---

## Installation Issues

### Python Version Error

**Problem:** `Python 3.10+ required`

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.10 or higher
# On Windows: Download from python.org
# On Mac: brew install python@3.11
# On Linux: sudo apt install python3.11
```

### Node Version Error

**Problem:** `Node.js 18+ required`

**Solution:**
```bash
# Check Node version
node --version

# Install Node 18+
# Using nvm:
nvm install 18
nvm use 18

# Or download from nodejs.org
```

### pip install fails

**Problem:** `ERROR: Could not build wheels for X`

**Solution:**
```bash
# Install build dependencies

# On Ubuntu/Debian:
sudo apt-get install python3-dev build-essential

# On Mac:
xcode-select --install

# On Windows:
# Install Visual Studio Build Tools
```

### npm install fails

**Problem:** `ERESOLVE unable to resolve dependency tree`

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install --legacy-peer-deps
```

---

## Backend Issues

### Backend won't start

**Problem:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Port 8000 already in use

**Problem:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
# On Mac/Linux:
lsof -i :8000
kill -9 <PID>

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
uvicorn main:app --port 8001
```

### Environment variables not loading

**Problem:** `KeyError: 'OPENAI_API_KEY'`

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check file contents
cat .env

# Ensure dotenv is installed
pip install python-dotenv

# Manually load and test
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### Database connection fails

**Problem:** `Could not connect to Supabase`

**Solution:**
1. Check Supabase credentials in .env
2. Verify Supabase project is active
3. Check network connectivity
4. Test connection:
```python
from supabase import create_client
import os

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase = create_client(url, key)
print("Connected!")
```

---

## Frontend Issues

### Next.js build fails

**Problem:** `Error: Failed to compile`

**Solution:**
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run build
```

### API calls fail with CORS error

**Problem:** `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:**

1. **Backend (main.py):** Ensure CORS is configured:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Check Frontend API URL:**
```javascript
// Should be http://localhost:8000, not https
const API_URL = "http://localhost:8000";
```

### Page not found (404)

**Problem:** `/demo` returns 404

**Solution:**
```bash
# Verify file exists
ls frontend/src/app/demo/page.tsx

# Restart dev server
npm run dev

# Clear browser cache
# Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

---

## API Issues

### API returns 500 error

**Problem:** `Internal Server Error`

**Solution:**

1. **Check backend logs:**
```bash
# Terminal running uvicorn will show error details
```

2. **Common causes:**
   - OpenAI API key invalid
   - Pinecone index doesn't exist
   - Database connection failed

3. **Test API health:**
```bash
curl http://localhost:8000/health
```

### API responds slowly

**Problem:** Responses take >10 seconds

**Solution:**

1. **Check OpenAI API status:** https://status.openai.com
2. **Verify Pinecone performance:**
   - Free tier has limits
   - Check index size
3. **Optimize chunks:**
   - Reduce chunk size in document_processor.py
   - Limit number of chunks retrieved (k=4 → k=2)

---

## Content Upload Issues

### PDF upload fails

**Problem:** `Error processing PDF`

**Solution:**

1. **Check file size:**
   - Max recommended: 50MB
   - Compress large PDFs

2. **Verify PDF is readable:**
```python
from langchain_community.document_loaders import PyPDFLoader
loader = PyPDFLoader("your-file.pdf")
docs = loader.load()
print(len(docs))
```

3. **Check for encrypted PDFs:**
   - Remove password protection first

### Video transcription fails

**Problem:** `Transcription error`

**Solution:**

1. **Supported formats:** MP4, MOV, AVI, M4A
2. **Max file size:** 25MB for Whisper API
3. **For large videos:**
   - Split video into smaller chunks
   - Or extract audio first:
```bash
ffmpeg -i input.mp4 -vn -acodec copy output.m4a
```

4. **Check OpenAI API quota:**
   - Transcription uses credits
   - Verify account has credits

### Content doesn't appear in search

**Problem:** Uploaded content but chat doesn't use it

**Solution:**

1. **Verify upload succeeded:**
```bash
# Check backend logs for "Processed X chunks"
```

2. **Check Pinecone:**
```python
from pinecone import Pinecone
pc = Pinecone(api_key="your-key")
index = pc.Index("creator-support-ai")
stats = index.describe_index_stats()
print(stats)  # Should show vectors
```

3. **Wait for indexing:**
   - Large files take time to process
   - Check if processing is complete

4. **Verify creator_id matches:**
   - Upload uses same creator_id as chat

---

## Chat Response Issues

### AI returns "I don't know"

**Problem:** AI can't answer even though content was uploaded

**Causes & Solutions:**

1. **Content not indexed yet:**
   - Wait a few minutes after upload
   - Check if processing completed

2. **Question doesn't match content:**
   - Rephrase question
   - Be more specific

3. **Low similarity threshold:**
   - Edit support_agent.py
   - Lower confidence requirements

4. **Wrong creator_id:**
   - Verify same creator_id for upload and chat

### No source citations

**Problem:** Response doesn't include sources

**Solution:**

Check vector_store.py returns scores:
```python
results = vectorstore.similarity_search_with_score(query, k=k)
# Should return [(doc, score), ...]
```

### Responses are inaccurate

**Problem:** AI gives wrong information

**Solutions:**

1. **Improve content quality:**
   - Use clear, well-formatted documents
   - Remove irrelevant content

2. **Adjust chunking:**
```python
# In document_processor.py
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Smaller chunks = more precise
    chunk_overlap=100,
)
```

3. **Review escalated responses:**
   - Check dashboard for flagged items
   - Improve knowledge base based on failures

---

## Deployment Issues

### Vercel deployment fails

**Problem:** `Build failed`

**Solution:**

1. **Check build locally:**
```bash
cd frontend
npm run build
```

2. **Common issues:**
   - Missing environment variables in Vercel
   - TypeScript errors
   - Import paths incorrect

3. **Verify environment variables:**
   - NEXT_PUBLIC_API_URL
   - NEXT_PUBLIC_SUPABASE_URL
   - NEXT_PUBLIC_SUPABASE_ANON_KEY

### Railway deployment fails

**Problem:** `Build error` or `Deployment crashed`

**Solution:**

1. **Check logs in Railway dashboard**

2. **Verify Dockerfile:**
```dockerfile
# Ensure all dependencies are installed
RUN pip install --no-cache-dir -r requirements.txt
```

3. **Environment variables:**
   - All required vars set in Railway
   - No typos in variable names

4. **Port configuration:**
```python
# main.py should use PORT from environment
import os
port = int(os.getenv("PORT", 8000))
```

### Database migrations fail

**Problem:** `Table already exists` or `Table not found`

**Solution:**

1. **Run schema.sql fresh:**
   - Drop existing tables
   - Run schema.sql in Supabase SQL editor

2. **Check RLS policies:**
   - Verify policies exist
   - Test with service role key

---

## Performance Issues

### Slow response times

**Problem:** Chat responses take >5 seconds

**Solutions:**

1. **Optimize vector search:**
```python
# Reduce number of chunks retrieved
results = await self.vector_store.similarity_search(
    query=query,
    creator_id=creator_id,
    k=2  # Instead of 4
)
```

2. **Use faster model:**
```python
# In support_agent.py
self.llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # Faster than gpt-4
    temperature=0.3,
)
```

3. **Add caching:**
   - Cache common queries
   - Use Redis for response cache

### High API costs

**Problem:** OpenAI bills too high

**Solutions:**

1. **Monitor usage:**
   - Check OpenAI dashboard
   - Identify expensive operations

2. **Optimize:**
   - Use smaller embeddings model
   - Reduce chunk sizes
   - Implement response caching

3. **Set usage limits:**
   - OpenAI dashboard → Usage limits
   - Set monthly budget

### Out of memory

**Problem:** Backend crashes with memory error

**Solutions:**

1. **Reduce batch size:**
```python
# Process files in smaller batches
# Don't load entire PDF at once
```

2. **Increase server resources:**
   - Railway: Upgrade plan
   - Docker: Increase memory limit

3. **Clean up resources:**
```python
# Close connections properly
# Use context managers
with open(file) as f:
    # process
```

---

## Diagnostic Commands

### Check all services

```bash
# Backend health
curl http://localhost:8000/health

# Frontend running
curl http://localhost:3000

# Pinecone connection
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='YOUR_KEY'); print(pc.list_indexes())"

# Supabase connection
python -c "from supabase import create_client; print('Connected!')"
```

### View logs

```bash
# Backend logs (if using uvicorn)
# Check terminal output

# Frontend logs
# Check browser console (F12)

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Reset everything

```bash
# Nuclear option - fresh start

# Stop all services
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Clear caches
rm -rf frontend/.next
rm -rf frontend/node_modules
rm -rf backend/__pycache__
rm -rf backend/venv

# Reinstall
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd frontend && npm install

# Restart
docker-compose up
```

---

## Getting Help

If issues persist:

1. **Check logs first** - Most errors show in terminal output
2. **Search GitHub issues** - Someone may have had same problem
3. **Create minimal reproduction** - Isolate the issue
4. **Gather information:**
   - Error messages (full text)
   - Steps to reproduce
   - Environment (OS, Python version, Node version)
   - Logs from backend and frontend

5. **Open an issue** with all above information

---

## Prevention Tips

1. **Use version validation script:**
```bash
python backend/validate_env.py --test-keys
```

2. **Regular health checks:**
```bash
# Add to cron or scheduled task
curl http://localhost:8000/health
```

3. **Monitor logs:**
   - Set up log aggregation
   - Use Sentry for error tracking

4. **Keep dependencies updated:**
```bash
pip list --outdated
npm outdated
```

5. **Backup regularly:**
   - Database backups
   - Environment variable backups
   - Content backups

---

*Last Updated: 2026-01-02*
