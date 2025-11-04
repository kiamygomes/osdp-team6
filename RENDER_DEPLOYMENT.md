# 🚀 Render Deployment Guide

## Quick Start (5 minutes)

### 1. Create Jira OAuth App
1. Go to [developer.atlassian.com](https://developer.atlassian.com) → Create OAuth 2.0 integration
2. Add callback URL: `https://osdp-jira-service.onrender.com/api/v1/auth/callback`
3. Set scopes: `read:jira-work`, `write:jira-work`, `read:jira-user`, `offline_access`
4. Save your **Client ID** and **Client Secret**

### 2. Deploy to Render
1. Push code to GitHub: `git push origin main`
2. Go to [render.com](https://render.com) → Sign up (free)
3. Click "New +" → "Blueprint" → Connect your GitHub repo
4. Render detects `render.yaml` → Click "Apply"

### 3. Set Environment Variables
In Render Dashboard → Your Service → Environment:
```
JIRA_CLIENT_ID=your_client_id_here
JIRA_CLIENT_SECRET=your_client_secret_here
```

### 4. Verify Deployment
- **API Docs**: `https://osdp-jira-service.onrender.com/docs`
- **OpenAPI Spec**: `https://osdp-jira-service.onrender.com/api/v1/openapi.json`
- **Health Check**: `https://osdp-jira-service.onrender.com/health`

## What Gets Created
- ✅ FastAPI web service (free tier: 750 hours/month)
- ✅ PostgreSQL database (1GB free)
- ✅ Automatic HTTPS certificates
- ✅ Auto-deployment on git push

## Free Tier Notes
- Service sleeps after 15 minutes of inactivity
- First request after sleep takes ~30-60 seconds
- Perfect for development and testing

## Troubleshooting
- **Build fails**: Check Render logs for missing dependencies
- **OAuth errors**: Verify callback URL matches exactly
- **Service won't start**: Ensure environment variables are set

Your OpenAPI spec will be available at:
`https://osdp-jira-service.onrender.com/api/v1/openapi.json`

Use this URL with your `openapi-python-client` generator! 🎉