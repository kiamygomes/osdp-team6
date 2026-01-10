# Authentication Architecture

This document explains how authentication works in the OSDP Ticket Bot Orchestrator.

## Overview

The orchestrator integrates three verticals:
- **Chat** (Discord/Slack) - Uses bot tokens from environment variables
- **AI** (Claude/OpenAI) - Uses API keys from environment variables
- **Tickets** (Jira/Trello) - Uses per-user OAuth 2.0

## Why Different Authentication Methods?

### Per-User OAuth (Tickets Only)
The ticket service requires per-user OAuth because:
- Each user has their own Jira account
- Different users have different permissions
- Tickets are user-specific

### Bot Tokens (Chat Services)
Chat services use bot tokens because:
- The bot acts on behalf of itself, not individual users
- Simpler for demo purposes
- Acceptable tradeoff per assignment requirements

### API Keys (AI Services)
AI services use API keys because:
- They don't have user-specific accounts
- Your backend makes requests on behalf of all users
- No OAuth supported by providers

## User Authentication Flow

### Step 1: User Visits the Orchestrator

```
User → GET https://your-orchestrator.onrender.com/auth/login?user_id=alice
```

Response:
```json
{
  "auth_url": "https://auth.atlassian.com/authorize?...",
  "message": "Please visit the auth_url to authorize with Jira",
  "user_id": "alice",
  "service": "jira"
}
```

### Step 2: User Authorizes with Jira

User clicks the `auth_url` and authorizes the application in their browser.

### Step 3: OAuth Callback

Jira redirects back to:
```
https://your-orchestrator.onrender.com/auth/callback?code=...&state=...
```

The orchestrator:
1. Validates the state parameter
2. Exchanges the code for access/refresh tokens
3. Stores tokens in the database with `service_name='jira'`

### Step 4: User Can Use the Orchestrator

```
POST https://your-orchestrator.onrender.com/process
{
  "message": "Create a ticket for fixing the login bug",
  "user_id": "alice",
  "project_key": "PROJ",
  "ai_provider": "claude"
}
```

## Environment Variables

### Required for Jira OAuth

```bash
# Jira OAuth Configuration
OAUTH_CLIENT_ID="your-atlassian-oauth-client-id"
OAUTH_CLIENT_SECRET="your-atlassian-oauth-client-secret"
OAUTH_REDIRECT_URI="https://your-orchestrator.onrender.com/auth/callback"
JIRA_CLOUD_ID="your-jira-cloud-id"
JIRA_PROJECT_KEY="PROJ"
```

### Required for Chat (Bot Tokens)

Both Slack and Discord implement the same `ChatInterface` ABC, making them interchangeable.

```bash
# Discord Bot Token (Option 1)
DISCORD_BOT_TOKEN="your-discord-bot-token"
DISCORD_CLIENT_ID="your-discord-client-id"
DISCORD_PUBLIC_KEY="your-discord-public-key"

# OR Slack Bot Token (Option 2)
SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"
SLACK_CLIENT_ID="your-slack-client-id"
SLACK_CLIENT_SECRET="your-slack-client-secret"

# Chat Provider Selection
CHAT_PROVIDER="discord"  # or "slack"
```

### Required for AI (API Keys)

Both Claude and OpenAI are supported and interchangeable.

```bash
# Claude AI (Option 1)
ANTHROPIC_API_KEY="your-claude-api-key"

# OR OpenAI (Option 2)
OPENAI_API_KEY="your-openai-api-key"

# AI Provider Selection (set in request or default)
AI_PROVIDER="claude"  # or "openai"
```

## Database Schema

The token storage supports multiple services per user:

```sql
CREATE TABLE jira_oauth_tokens (
    user_id TEXT NOT NULL,
    service_name TEXT NOT NULL DEFAULT 'jira',
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (user_id, service_name)
);
```

This allows future expansion to store OAuth tokens for other services (Slack, Discord, etc.) if needed.

## API Endpoints

### Authentication Endpoints

#### GET /auth/login
Start OAuth flow for a user.

**Query Parameters:**
- `user_id` (optional, default: "demo_user")

**Response:**
```json
{
  "auth_url": "https://auth.atlassian.com/authorize?...",
  "message": "Please visit the auth_url to authorize with Jira",
  "user_id": "alice",
  "service": "jira"
}
```

#### GET /auth/callback
OAuth callback endpoint (handled automatically by OAuth flow).

**Query Parameters:**
- `code` (from OAuth provider)
- `state` (CSRF protection)

**Response:**
```json
{
  "message": "Jira authentication successful!",
  "user_id": "alice",
  "service": "jira",
  "authenticated": "true"
}
```

#### GET /auth/status
Check if a user is authenticated.

**Query Parameters:**
- `user_id` (optional, default: "demo_user")

**Response:**
```json
{
  "authenticated": true,
  "user_id": "alice",
  "has_valid_tokens": true,
  "message": "User 'alice' is authenticated with Jira and ready to use the orchestrator."
}
```

## Deployment Configuration

### 1. Configure OAuth App in Atlassian

1. Go to https://developer.atlassian.com/console/myapps/
2. Create an OAuth 2.0 integration
3. Set the callback URL to: `https://your-orchestrator.onrender.com/auth/callback`
4. Note the Client ID and Client Secret

### 2. Set Environment Variables on Render

In your Render dashboard, set:
- `OAUTH_CLIENT_ID`
- `OAUTH_CLIENT_SECRET`
- `OAUTH_REDIRECT_URI=https://your-orchestrator.onrender.com/auth/callback`
- All other required environment variables

### 3. Deploy

The orchestrator will:
- Start without any user tokens stored
- Users authenticate via `/auth/login` when they first use it
- Tokens are stored in the SQLite database
- Database persists across deployments on Render's persistent disk

## Security Considerations

### State Parameter
The OAuth flow uses a cryptographically random state parameter to prevent CSRF attacks.

### Token Storage
Tokens are stored in SQLite with:
- Encrypted at rest (Render's disk encryption)
- Never committed to Git (database file is in `.gitignore`)
- Automatic expiry checking

### Token Refresh
Tokens are automatically refreshed when expired using the refresh token.

## Testing Locally

1. Start the orchestrator:
   ```bash
   cd src/orchestrator
   uvicorn orchestrator.orchestrator_service:app --reload
   ```

2. Visit http://localhost:8000/auth/login

3. Follow the OAuth flow

4. Test with:
   ```bash
   curl -X POST http://localhost:8000/process \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Show me my tickets",
       "user_id": "demo_user"
     }'
   ```

## Troubleshooting

### "User has no auth tokens"
**Solution:** User needs to complete OAuth flow via `/auth/login`

### "Invalid state parameter"
**Solution:** The state parameter expired or was invalid. Start a new OAuth flow.

### "OAuth callback failed"
**Solution:** Check that:
- `OAUTH_REDIRECT_URI` matches exactly what's configured in Atlassian
- `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` are correct
- The OAuth app has the correct scopes enabled

## Future Enhancements

The current architecture supports adding OAuth for other services:

```python
# Store Slack OAuth tokens
upsert_tokens(user_id, access, refresh, expires_in, service_name="slack")

# Store Discord OAuth tokens
upsert_tokens(user_id, access, refresh, expires_in, service_name="discord")

# Retrieve service-specific tokens
slack_tokens = get_tokens(user_id, service_name="slack")
discord_tokens = get_tokens(user_id, service_name="discord")
```

This allows the orchestrator to manage multi-service OAuth as needed.
