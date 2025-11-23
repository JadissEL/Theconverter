# Deployment Guide

## Vercel Deployment

### Prerequisites

1. GitHub account
2. Vercel account (sign up at vercel.com)
3. Git repository for your project

### Step-by-Step Deployment

#### 1. Prepare Repository

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/theconverter.git
git push -u origin main
```

#### 2. Connect to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure project:
   - Framework Preset: **Next.js**
   - Root Directory: `./`
   - Build Command: `npm run build`
   - Output Directory: `.next`

#### 3. Environment Variables

Add these in Vercel dashboard:

```
MAX_FILE_SIZE=524288000
```

#### 4. Deploy

Click "Deploy" and wait for the build to complete.

### Important Limitations

⚠️ **Vercel Serverless Limitations:**

1. **Deployment Size**: 250MB limit (FFmpeg is ~100MB)
2. **Function Duration**: Max 300 seconds on Pro plan
3. **Memory**: Max 3008MB
4. **File System**: Read-only (use /tmp for temporary files)

### Alternative Deployment Options

#### Option 1: Railway (Recommended for Media Processing)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

**Advantages:**
- No size limits
- Persistent storage
- Better for FFmpeg workloads
- Simple Docker deployment

#### Option 2: Render

1. Create `Dockerfile`:

```dockerfile
FROM node:18-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM python:3.9-slim
RUN apt-get update && apt-get install -y ffmpeg libmagic1 nodejs npm
WORKDIR /app
COPY --from=frontend /app/.next ./.next
COPY --from=frontend /app/public ./public
COPY --from=frontend /app/node_modules ./node_modules
COPY api/ ./api/
RUN pip install -r api/requirements.txt
CMD ["sh", "-c", "cd api && uvicorn main:app --host 0.0.0.0 --port $PORT"]
```

2. Deploy to Render:
   - Connect GitHub repository
   - Select Docker as environment
   - Deploy

#### Option 3: AWS Lambda with Layers

1. Create FFmpeg Lambda Layer
2. Deploy FastAPI with Mangum adapter
3. Use S3 for file storage
4. CloudFront for frontend

#### Option 4: Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/theconverter

# Deploy
gcloud run deploy theconverter \
  --image gcr.io/PROJECT_ID/theconverter \
  --platform managed \
  --memory 4Gi \
  --timeout 300
```

## Production Considerations

### 1. File Storage

Use cloud storage instead of temporary files:

```bash
npm install @vercel/blob
# or
npm install @aws-sdk/client-s3
# or
npm install @google-cloud/storage
```

### 2. Queue System

For long conversions, implement a queue:

```bash
npm install bull redis
```

### 3. Monitoring

Add monitoring and logging:

```bash
npm install @sentry/nextjs
npm install @vercel/analytics
```

### 4. CDN Configuration

Enable Vercel Edge Network:
- Automatic for static assets
- Configure in `next.config.js` for API routes

### 5. Rate Limiting

Implement rate limiting:

```python
# api/middleware/rate_limit.py
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/convert")
@limiter.limit("10/minute")
async def convert_file(request: Request, ...):
    ...
```

## Environment Variables

### Production Environment Variables

```bash
# Required
NODE_ENV=production
PYTHON_ENV=production

# Optional
MAX_FILE_SIZE=524288000
ALLOWED_ORIGINS=https://yourdomain.com
BLOB_READ_WRITE_TOKEN=your_token_here
REDIS_URL=redis://your-redis-url
SENTRY_DSN=your_sentry_dsn
```

## Custom Domain Setup

1. **Vercel:**
   - Go to Project Settings → Domains
   - Add your domain
   - Update DNS records

2. **SSL Certificate:**
   - Automatic with Vercel
   - Free Let's Encrypt certificate

## Performance Optimization

### 1. Enable Compression

Already enabled in Next.js by default.

### 2. Image Optimization

```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['yourdomain.com'],
    formats: ['image/avif', 'image/webp'],
  },
}
```

### 3. Caching Strategy

```javascript
// Cache converted files
export const revalidate = 3600; // 1 hour
```

### 4. Code Splitting

Next.js handles this automatically with dynamic imports.

## Monitoring & Logs

### Vercel Logs

```bash
vercel logs [deployment-url]
```

### Custom Logging

```python
# api/utils/logger.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

## Backup & Recovery

1. **Database Backups**: If using database, enable automated backups
2. **File Storage**: Enable versioning on cloud storage
3. **Code Repository**: Regular commits to GitHub

## Security Best Practices

1. **API Security**:
   - Implement rate limiting
   - Validate file types
   - Scan for malware
   - Set file size limits

2. **CORS Configuration**:
   - Restrict allowed origins in production
   - Use environment variables for domains

3. **Environment Variables**:
   - Never commit `.env` files
   - Use Vercel's environment variables
   - Rotate secrets regularly

## Troubleshooting Deployment

### Build Fails

```bash
# Check build logs
vercel logs

# Local build test
npm run build
```

### Function Timeout

- Increase timeout in `vercel.json`
- Optimize conversion code
- Consider worker queue

### Out of Memory

- Increase memory in `vercel.json`
- Optimize file handling
- Use streaming where possible

## Cost Estimation

### Vercel Pricing (as of 2024)

- **Hobby**: Free (limited)
- **Pro**: $20/month
  - 1,000 hours serverless function execution
  - 100GB bandwidth
  - 1,000GB-hours edge middleware

### Alternative Platforms

- **Railway**: ~$5-20/month (pay for usage)
- **Render**: Free tier + $7/month for 512MB
- **AWS Lambda**: Pay per request (~$0.20 per million)
- **Google Cloud Run**: Pay per use (~$0.24 per million)

## Rollback Strategy

```bash
# List deployments
vercel ls

# Promote previous deployment
vercel promote [deployment-url]

# Rollback via dashboard
# Go to Deployments → Select → Promote to Production
```
