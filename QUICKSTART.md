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

## Adding the Embed Widget to Your Website (For Beginners)

The embed widget lets you add AI chat support to ANY website. Here's exactly where to put the code:

### Step 1: Get Your Embed Code

1. Go to your dashboard at `https://never-afk-ai-lngm.vercel.app/dashboard`
2. Click "Embed Widget" tab
3. Customize colors and position
4. Copy the code snippet

### Step 2: Add to Your Website

The code looks like this:
```html
<!-- Creator Support AI Widget -->
<script>
  (function() {
    var script = document.createElement('script');
    script.src = 'https://never-afk-ai-lngm.vercel.app/embed.js';
    script.setAttribute('data-creator-id', 'YOUR-ID-HERE');
    script.setAttribute('data-position', 'bottom-right');
    script.setAttribute('data-color', '#8b5cf6');
    script.setAttribute('data-welcome', 'Hi! How can I help you today?');
    script.async = true;
    document.head.appendChild(script);
  })();
</script>
```

### Where to Paste It (By Platform)

#### WordPress
1. Go to **Appearance > Theme Editor**
2. Open `footer.php`
3. Paste the code BEFORE `</body>`
4. Click "Update File"

**Or use a plugin:**
1. Install "Insert Headers and Footers" plugin
2. Go to Settings > Insert Headers and Footers
3. Paste in "Scripts in Footer" section
4. Save

#### Squarespace
1. Go to **Settings > Advanced > Code Injection**
2. Paste in the "Footer" section
3. Save

#### Wix
1. Go to **Settings > Custom Code**
2. Click "+ Add Custom Code"
3. Paste the code
4. Set placement to "Body - end"
5. Apply to "All pages"

#### Shopify
1. Go to **Online Store > Themes**
2. Click "Actions" > "Edit code"
3. Open `theme.liquid`
4. Paste BEFORE `</body>`
5. Save

#### HTML Website
Open your HTML file and paste before `</body>`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>My Website</title>
</head>
<body>
    <!-- Your website content here -->

    <!-- Paste the embed code HERE, before </body> -->
    <script>
      (function() {
        var script = document.createElement('script');
        script.src = 'https://never-afk-ai-lngm.vercel.app/embed.js';
        script.setAttribute('data-creator-id', 'YOUR-ID-HERE');
        script.setAttribute('data-position', 'bottom-right');
        script.setAttribute('data-color', '#8b5cf6');
        script.setAttribute('data-welcome', 'Hi! How can I help you today?');
        script.async = true;
        document.head.appendChild(script);
      })();
    </script>
</body>
</html>
```

#### React/Next.js
Add to your `_app.js` or layout component:
```jsx
import Script from 'next/script';

export default function App({ Component, pageProps }) {
  return (
    <>
      <Component {...pageProps} />
      <Script
        id="creator-ai-widget"
        strategy="lazyOnload"
        dangerouslySetInnerHTML={{
          __html: `
            (function() {
              var script = document.createElement('script');
              script.src = 'https://never-afk-ai-lngm.vercel.app/embed.js';
              script.setAttribute('data-creator-id', 'YOUR-ID-HERE');
              script.setAttribute('data-position', 'bottom-right');
              script.setAttribute('data-color', '#8b5cf6');
              script.async = true;
              document.head.appendChild(script);
            })();
          `,
        }}
      />
    </>
  );
}
```

### Verify It's Working

1. Refresh your website
2. Look for the chat button in the corner you selected
3. Click it and send a test message
4. You should get a response based on your uploaded content!

### Troubleshooting Embed Widget

**Widget doesn't appear:**
- Make sure code is before `</body>`, not in `<head>`
- Clear your browser cache
- Check browser console for errors (F12)

**"Error" message when chatting:**
- Verify your creator ID is correct
- Make sure you've uploaded content first
- Check if backend is running

---

## Next Steps

1. **Upload more content**: PDFs, videos, etc.
2. **Customize the UI**: Edit components in `frontend/src/components/`
3. **Set up Supabase**: For persistent storage and auth
4. **Configure billing**: Add Lemon Squeezy integration
5. **Deploy**: Use Vercel for frontend, Railway for backend

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
