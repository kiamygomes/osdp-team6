# E2E Test Setup Guide

## Quick Start

### Option 1: Use Existing Tokens from CI/CD

If you have access to CircleCI environment variables:

```bash
# Get tokens from CircleCI and generate local tokens
python scripts/generate_e2e_tokens.py --tokens "$OAUTH_ACCESS_TOKEN" "$OAUTH_REFRESH_TOKEN" 3600
```

### Option 2: Get Fresh Tokens from Deployed Service

1. **Login to deployed service:**
   ```bash
   open https://osdp-team6.onrender.com/api/v1/auth/login
   ```
   
   This will:
   - Redirect you to Jira OAuth
   - After authorization, store tokens in the deployed database
   - Show you your user ID

2. **Update your `.env` file:**
   ```bash
   # Copy the user ID from the auth status page
   OAUTH_USER_ID="your-user-id-here"
   ```

3. **For local workflow tests**, you need to copy tokens from the deployed database to local:
   
   Unfortunately, there's no API endpoint to export tokens (security). You have two options:
   
   **A. Use the same user ID for both:**
   - Set `OAUTH_USER_ID` in `.env` to your deployed user ID
   - Run deployed tests only (they use the deployed database)
   
   **B. Get tokens from CircleCI:**
   - Ask your team for the `OAUTH_ACCESS_TOKEN` and `OAUTH_REFRESH_TOKEN` from CI/CD
   - Run: `python scripts/generate_e2e_tokens.py --tokens "$ACCESS" "$REFRESH" 3600`

## Running Tests

### Deployed Tests Only (Recommended)

```bash
# Make sure BASE_URL is not set to localhost
unset BASE_URL

# Run deployed tests
uv run pytest tests/e2e/test_e2e_deployed.py -v --no-cov
```

These tests hit the live deployed service at `https://osdp-team6.onrender.com`.

### Workflow Tests (Requires Local Tokens)

```bash
# First, generate local tokens (see Option 2B above)
python scripts/generate_e2e_tokens.py --tokens "$ACCESS_TOKEN" "$REFRESH_TOKEN" 3600

# Run workflow tests
uv run pytest tests/e2e/test_e2e_workflows.py -v --no-cov
```

### All E2E Tests

```bash
uv run pytest tests/e2e/ -v --no-cov
```

## Troubleshooting

### 401 Unauthorized Errors

Your OAuth tokens have expired. Refresh them:

**For deployed tests:**
```bash
open https://osdp-team6.onrender.com/api/v1/auth/login
```

**For workflow tests:**
```bash
python scripts/generate_e2e_tokens.py --tokens "$ACCESS_TOKEN" "$REFRESH_TOKEN" 3600
```

### 500 Internal Server Error

Usually means tokens exist but are invalid/expired on Jira's side. Follow the 401 fix above.

### Connection Refused

Check if `BASE_URL` environment variable is set to localhost:
```bash
echo $BASE_URL
# If it shows localhost:8000, unset it:
unset BASE_URL
```

## Token Expiry

- OAuth tokens typically expire after 1 hour
- Refresh tokens can be used to get new access tokens
- The deployed service automatically refreshes tokens when needed
- Local tests need manual token refresh

## Security Note

Never commit tokens to git! They are stored in:
- Deployed: PostgreSQL database on Render
- Local: `jira_tokens.db` (gitignored)
