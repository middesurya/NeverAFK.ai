# Deployment Guide - Creator Support AI

Complete guide for deploying your RAG-powered support system to production.

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Vercel    │────▶│   Railway    │────▶│  Pinecone   │
│  (Frontend) │     │  (Backend)   │     │  (Vectors)  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Supabase   │
                    │ (PostgreSQL) │
                    └──────────────┘
```

## Prerequisites

- [ ] GitHub account
- [ ] Vercel account
- [ ] Railway or Render account
- [ ] Pinecone account (free tier works)
- [ ] Supabase account (free tier works)
- [ ] OpenAI API key with credits
- [ ] Lemon Squeezy account (for payments)
- [ ] Custom domain (optional)

## Step 1: Database Setup (Supabase)

### Create Project

1. Go to https://supabase.com
2. Click "New Project"
3. Name: `creator-support-ai`
4. Generate a strong database password
5. Choose region closest to your users
6. Wait for project to initialize (~2 minutes)

### Run SQL Schema

1. Go to SQL Editor
2. Click "New Query"
3. Copy contents from `backend/schema.sql`
4. Click "Run"
5. Verify tables created: `creators`, `content_uploads`, `conversations`

### Get Credentials

1. Go to Settings > API
2. Copy:
   - Project URL (SUPABASE_URL)
   - Anon/Public Key (SUPABASE_ANON_KEY)
   - Service Role Key (SUPABASE_SERVICE_KEY)

## Step 2: Vector Store Setup (Pinecone)

### Create Index

1. Go to https://app.pinecone.io
2. Click "Create Index"
3. Settings:
   - Name: `creator-support-ai`
   - Dimensions: `1536`
   - Metric: `cosine`
   - Cloud Provider: `AWS`
   - Region: `us-east-1`
4. Click "Create Index"

### Get API Key

1. Go to API Keys
2. Copy your API key
3. Note your environment (e.g., `us-east-1-aws`)

## Step 3: Backend Deployment (Railway)

### Option A: Railway (Recommended)

1. Push code to GitHub
2. Go to https://railway.app
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Select `backend` directory

### Configure Environment Variables

Add these in Railway dashboard:

```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
LEMON_SQUEEZY_API_KEY=...
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend-domain.vercel.app
```

### Deploy Configuration

Create `railway.json` in backend directory:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

### Custom Domain (Optional)

1. In Railway, go to Settings
2. Click "Generate Domain"
3. Or add custom domain: `api.yourdomain.com`

### Option B: Render

1. Go to https://render.com
2. Click "New +" > "Web Service"
3. Connect GitHub repository
4. Settings:
   - Name: `creator-support-ai-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)

## Step 4: Frontend Deployment (Vercel)

### Deploy to Vercel

1. Push code to GitHub
2. Go to https://vercel.com
3. Click "New Project"
4. Import your GitHub repository
5. Settings:
   - Framework Preset: Next.js
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

### Environment Variables

Add in Vercel dashboard:

```
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

### Custom Domain

1. Go to Project Settings > Domains
2. Add your domain: `app.yourdomain.com`
3. Follow DNS configuration instructions
4. Wait for SSL certificate (automatic)

## Step 5: Configure CORS

Update backend environment variable:

```
CORS_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
```

Redeploy backend after updating.

## Step 6: Set Up Monitoring

### Backend Monitoring

Railway/Render provide built-in:
- Logs
- Metrics
- Uptime monitoring

### Frontend Monitoring

Vercel provides:
- Analytics
- Real User Monitoring
- Error tracking

### Additional Tools

**Sentry** (Error Tracking):
1. Sign up at https://sentry.io
2. Create new project
3. Add Sentry SDK to both frontend and backend
4. Configure DSN in environment variables

**LogTail** (Log Management):
1. Sign up at https://logtail.com
2. Create source
3. Add logging integration

## Step 7: Performance Optimization

### Backend

1. **Enable Caching**:
   - Add Redis for response caching
   - Cache vector search results

2. **Database Connection Pooling**:
   - Configure Supabase connection pool
   - Use PgBouncer for connection management

3. **Rate Limiting**:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

### Frontend

1. **Enable Static Generation** where possible
2. **Image Optimization** (use Next.js Image component)
3. **Code Splitting** (automatic with Next.js)
4. **CDN Caching** (automatic with Vercel)

## Step 8: Security Checklist

- [ ] Environment variables configured (no secrets in code)
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection (React's built-in escaping)
- [ ] HTTPS enabled (automatic with Vercel/Railway)
- [ ] Supabase RLS policies enabled
- [ ] API key rotation schedule set
- [ ] Backup strategy configured

## Step 9: Post-Deployment

### Smoke Tests

Run these tests after deployment:

1. **Health Check**:
   ```bash
   curl https://your-api.com/health
   ```

2. **Upload Content**:
   Use the UI to upload test content

3. **Test Chat**:
   Ask a question and verify response

4. **Check Conversations**:
   Verify conversations are saved in Supabase

### Set Up Backups

**Supabase Backups**:
- Go to Database > Backups
- Enable automatic daily backups
- Configure retention period

**Pinecone Backups**:
- Export index regularly
- Store backups in S3

### Monitor Costs

**OpenAI**:
- Set spending limits
- Monitor usage at https://platform.openai.com/usage

**Pinecone**:
- Watch for index size
- Optimize vector dimensions if needed

**Supabase**:
- Monitor database size
- Track API requests

**Railway/Render**:
- Monitor compute hours
- Optimize resource usage

## Scaling Considerations

### When to Scale

Watch these metrics:
- Response time > 2 seconds
- Error rate > 1%
- CPU usage > 80%
- Memory usage > 80%

### Horizontal Scaling

**Backend**:
- Add more Railway/Render instances
- Use load balancer (automatic with Railway)

**Database**:
- Upgrade Supabase plan
- Add read replicas

**Vector Store**:
- Upgrade Pinecone plan
- Use pod-based indexes for better performance

### Vertical Scaling

**Backend**:
- Increase Railway instance size
- More CPU/RAM for heavy processing

**Database**:
- Larger Supabase instance
- More connections

## Troubleshooting

### Common Issues

**"502 Bad Gateway"**:
- Check backend logs
- Verify environment variables
- Restart backend service

**"CORS Error"**:
- Verify CORS_ORIGINS includes your frontend URL
- Check frontend is using correct API URL

**"Database Connection Failed"**:
- Verify Supabase credentials
- Check if IP is whitelisted
- Verify database is running

**"Vector Search Not Working"**:
- Verify Pinecone index exists
- Check API key and environment
- Ensure content was uploaded successfully

### Rollback Strategy

**Frontend**:
1. Go to Vercel dashboard
2. Deployments > Previous deployment
3. Click "Promote to Production"

**Backend**:
1. Railway: Deployments > Select previous
2. Click "Redeploy"

## Cost Optimization

### Free Tier Limits

**Vercel**:
- 100GB bandwidth/month
- Unlimited deployments

**Railway**:
- $5 credit/month free

**Supabase**:
- 500MB database
- 2GB bandwidth
- 50,000 monthly active users

**Pinecone**:
- 1 free index
- Up to 100,000 vectors

### Optimization Tips

1. **Cache Aggressively**: Reduce OpenAI API calls
2. **Batch Operations**: Group vector searches
3. **Lazy Loading**: Load content on demand
4. **Optimize Images**: Use WebP format
5. **Minimize Bundle**: Tree shake unused code

## Production Checklist

- [ ] All services deployed and running
- [ ] Custom domains configured
- [ ] SSL certificates active
- [ ] Environment variables set correctly
- [ ] Database migrations run
- [ ] Smoke tests passed
- [ ] Monitoring configured
- [ ] Error tracking active
- [ ] Backups enabled
- [ ] Cost alerts configured
- [ ] Documentation updated
- [ ] Team access configured
- [ ] **⚠️ SMTP configured for Supabase emails** (see below)

## Email Configuration (CRITICAL for Production)

Supabase's built-in email service has strict rate limits (3-4 emails/hour) and is NOT suitable for production.

### Set Up Custom SMTP

1. Go to Supabase Dashboard → Project Settings → Authentication → SMTP Settings
2. Click "Set up SMTP"
3. Enter your SMTP credentials from one of these providers:

| Provider | Free Tier | Sign Up |
|----------|-----------|---------|
| **Resend** | 3,000/month | https://resend.com |
| **SendGrid** | 100/day | https://sendgrid.com |
| **Mailgun** | 5,000/month (3mo) | https://mailgun.com |
| **Postmark** | 100/month | https://postmarkapp.com |

### Required SMTP Settings
```
SMTP Host: (from provider)
SMTP Port: 587 (or 465 for SSL)
SMTP User: (from provider)
SMTP Password: (from provider)
Sender Email: noreply@yourdomain.com
Sender Name: Creator Support AI
```

### Emails Affected
- Signup confirmation
- Password reset
- Magic link login
- Email change verification

## Support

For deployment issues:
- Railway: https://railway.app/help
- Vercel: https://vercel.com/support
- Supabase: https://supabase.com/support
- Pinecone: https://www.pinecone.io/support/
