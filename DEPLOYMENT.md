# Deployment Guide: OSDP Ticket Bot Orchestrator

This guide walks you through deploying the 3-vertical integration application (Chat → AI → Tickets) to Render.

## Prerequisites

Before deploying, ensure you have:

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code pushed to GitHub
3. **Jira OAuth Credentials**:
   - `OAUTH_CLIENT_ID`
   - `OAUTH_CLIENT_SECRET`
   - `JIRA_CLOUD_ID`
   - Jira project key (e.g., `DEMO`)
4. **AI Provider API Keys**:
   - `ANTHROPIC_API_KEY` (for Claude)
   - `OPENAI_API_KEY` (for OpenAI)

---

## Step 1: Prepare Your Repository

1. **Commit all changes**:
   ```bash
   git add .
   git commit -m "feat: add orchestrator service for deployment"
   git push origin hw3-application
   ```

2. **Ensure submodules are included**:
   ```bash
   git submodule update --init --recursive
   git add .gitmodules external/
   git commit -m "fix: ensure submodules are tracked"
   git push
   ```

---

## Step 2: Deploy to Render

### Option A: Using Render Dashboard (Recommended)

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository: `osdp-team6`
   - Select branch: `hw3-application`

3. **Configure Service**:
   - **Name**: `osdp-ticket-bot-orchestrator`
   - **Environment**: `Docker`
   - **Region**: Choose closest to you (e.g., `Oregon (US West)`)
   - **Branch**: `hw3-application`
   - **Dockerfile Path**: `Dockerfile.orchestrator`
   - **Docker Build Context**: `.` (root directory)

4. **Configure Build Settings**:
   - **Build Command**: Leave empty (Docker handles this)
   - **Start Command**: Leave empty (Dockerfile CMD handles this)

5. **Instance Type**:
   - Select **Free** tier for testing
   - (Upgrade to Starter for production)

6. **Advanced Settings**:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Yes (recommended)

7. **Environment Variables** (Add these in the Environment section):

   ```bash
   # Jira Configuration
   OAUTH_CLIENT_ID=<your-jira-oauth-client-id>
   OAUTH_CLIENT_SECRET=<your-jira-oauth-client-secret>
   JIRA_CLOUD_ID=<your-jira-cloud-id>
   JIRA_PROJECT_KEY=DEMO  # or your project key
   OAUTH_REDIRECT_URI=https://osdp-ticket-bot-orchestrator.onrender.com/api/v1/auth/callback

   # AI Provider API Keys
   ANTHROPIC_API_KEY=<your-claude-api-key>
   OPENAI_API_KEY=<your-openai-api-key>

   # Service Configuration
   ENVIRONMENT=production
   PORT=8080
   LOG_LEVEL=INFO
   PYTHONUNBUFFERED=1
   DEFAULT_AI_PROVIDER=claude

   # Database (SQLite for now)
   DB_URL=sqlite:///./data/jira_tokens.db
   ```

   **Security Note**: Mark sensitive variables (API keys, secrets) as "Secret" in Render.

8. **Click "Create Web Service"**

9. **Wait for Deployment**:
   - Render will:
     - Clone your repository
     - Initialize git submodules
     - Build the Docker image
     - Deploy the container
   - First deployment takes ~5-10 minutes

### Option B: Using Render Blueprint (render.yaml)

1. **In Render Dashboard**:
   - Click "New +" → "Blueprint"
   - Select your repository
   - Choose `render-orchestrator.yaml`
   - Click "Apply"

2. **Set Environment Variables**:
   - Render will prompt you to set the `sync: false` variables
   - Fill in your API keys and OAuth credentials

3. **Click "Apply"** to deploy

---

## Step 3: Verify Deployment

Once deployment is complete:

1. **Check Service Status**:
   - Go to your service in Render dashboard
   - Status should show "Live" with a green indicator
   - Note your service URL: `https://osdp-ticket-bot-orchestrator.onrender.com`

2. **Test Health Endpoint**:
   ```bash
   curl https://osdp-ticket-bot-orchestrator.onrender.com/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "ticket-bot-orchestrator",
     "version": "1.0.0"
   }
   ```

3. **Check Service Status**:
   ```bash
   curl https://osdp-ticket-bot-orchestrator.onrender.com/status
   ```

   Expected response:
   ```json
   {
     "service": "ticket-bot-orchestrator",
     "version": "1.0.0",
     "environment": "production",
     "ai_provider_available": {
       "claude": true,
       "openai": true
     },
     "chat_available": false,
     "ticket_service_available": true
   }
   ```

4. **View Logs**:
   - In Render dashboard → Your service → "Logs" tab
   - Look for:
     ```
     ✅ Claude AI provider available
     ✅ OpenAI AI provider available
     Service started successfully
     ```

---

## Step 4: Test 3-Vertical Integration

### Test with Claude AI Provider

```bash
curl -X POST https://osdp-ticket-bot-orchestrator.onrender.com/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a ticket for fixing the login bug with high priority",
    "user_id": "demo_user",
    "project_key": "DEMO",
    "ai_provider": "claude"
  }'
```

Expected response:
```json
{
  "success": true,
  "message": "Created ticket: Fix login bug",
  "data": {
    "id": "...",
    "title": "Fix login bug",
    "status": "open",
    "priority": "high"
  },
  "error": null,
  "ai_provider": "claude",
  "user_id": "demo_user",
  "project_key": "DEMO"
}
```

### Test with OpenAI Provider (Provider Switching)

```bash
curl -X POST https://osdp-ticket-bot-orchestrator.onrender.com/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all open tickets",
    "user_id": "demo_user",
    "project_key": "DEMO",
    "ai_provider": "openai"
  }'
```

### Test Error Handling

```bash
curl -X POST https://osdp-ticket-bot-orchestrator.onrender.com/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a ticket",
    "user_id": "invalid_user",
    "project_key": "INVALID",
    "ai_provider": "claude"
  }'
```

---

## Step 5: Update OAuth Redirect URI

**Important**: After deployment, you need to update your Jira OAuth app settings:

1. Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Select your OAuth 2.0 app
3. Go to "Authorization" → "OAuth 2.0 (3LO)"
4. Add callback URL:
   ```
   https://osdp-ticket-bot-orchestrator.onrender.com/api/v1/auth/callback
   ```
5. Save changes

---

## Step 6: Monitor Your Deployment

### View Real-Time Logs

```bash
# In Render dashboard, go to Logs tab
# Or use Render CLI:
render logs -s osdp-ticket-bot-orchestrator --tail
```

### Check Metrics

Render provides built-in metrics:
- CPU usage
- Memory usage
- Request count
- Response times

Access at: Dashboard → Your Service → Metrics

### Custom Prometheus Metrics

If you add Prometheus middleware to the orchestrator service:
```
https://osdp-ticket-bot-orchestrator.onrender.com/metrics
```

---

## Troubleshooting

### Build Fails: "Submodules not found"

**Solution**: Ensure `.gitmodules` is committed:
```bash
git add .gitmodules
git commit -m "fix: add gitmodules"
git push
```

### Build Fails: "uv sync failed"

**Solution**: Check `pyproject.toml` and `uv.lock` are in sync:
```bash
uv sync --all-packages
git add uv.lock
git commit -m "fix: update lockfile"
git push
```

### Service Crashes: "AI provider not available"

**Solution**: Check environment variables in Render dashboard:
- Verify `ANTHROPIC_API_KEY` is set correctly
- Verify `OPENAI_API_KEY` is set correctly

### Database Error: "Unable to write to database"

**Solution**: Ensure `/app/data` directory has write permissions.

For production, use PostgreSQL:
1. Add database in Render
2. Update `DB_URL` to use the PostgreSQL connection string

### OAuth Errors: "Invalid redirect URI"

**Solution**:
1. Check `OAUTH_REDIRECT_URI` matches your Render URL exactly
2. Verify the URI is registered in Atlassian Developer Console

---

## Production Checklist

Before going to production:

- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS (Render does this automatically)
- [ ] Set up proper CORS origins (not `["*"]`)
- [ ] Add rate limiting
- [ ] Set up monitoring/alerting
- [ ] Configure auto-scaling
- [ ] Add health check notifications
- [ ] Review security settings
- [ ] Set up backup/restore procedures
- [ ] Configure custom domain (optional)

---

## Cost Estimate

**Free Tier (For Testing)**:
- Web Service: Free (750 hours/month)
- Spins down after 15 min of inactivity
- Spins up on request (~30s delay)

**Starter Tier (For Production)**:
- Web Service: $7/month
- Always on (no spin down)
- 512 MB RAM
- PostgreSQL: $7/month (optional)

---

## Next Steps

After successful deployment:

1. **Write E2E Tests**: Test against the live deployed service
2. **Create Video Demo**: Show the deployed application working
3. **Update README**: Add deployment URL and instructions
4. **Configure CI/CD**: Auto-deploy on push to main branch

---

## Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Your Service URL**: https://osdp-ticket-bot-orchestrator.onrender.com
