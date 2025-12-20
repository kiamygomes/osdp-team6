# Scripts

Utility scripts for development, testing, deployment, and setup tasks.

## Scripts

### `deploy.sh`
Deployment script for building and deploying the application.

**Usage:**
```bash
./scripts/deploy.sh
```

**What it does:**
- Builds Docker images for the application
- Pushes images to container registry
- Updates deployment configurations
- Handles environment-specific deployments

**Environment variables:**
- `DEPLOY_ENV`: Target environment (dev, staging, prod)
- `REGISTRY`: Container registry URL
- `IMAGE_TAG`: Tag for the container image

### `fix_slack_packages.sh`
Utility script to fix and patch Slack integration packages.

**Usage:**
```bash
./scripts/fix_slack_packages.sh
```

**What it does:**
- Patches Slack client dependencies
- Fixes compatibility issues
- Updates package configurations
- Ensures proper imports

**Prerequisites:**
- Slack team packages installed
- Python virtual environment activated

### `generate_e2e_tokens.py`
Generates OAuth tokens for end-to-end testing.

**Usage:**
```bash
uv run scripts/generate_e2e_tokens.py
```

**What it does:**
- Creates test OAuth tokens for Jira
- Generates test user sessions
- Stores tokens in database for testing
- Supports multiple test scenarios

**Output:**
- `test_tokens.db`: SQLite database with test tokens
- Console output showing generated token information

**Configuration:**
```python
# Set environment variables before running
OAUTH_CLIENT_ID = "test-client-id"
OAUTH_CLIENT_SECRET = "test-client-secret"
JIRA_CLOUD_ID = "test-cloud-id"
```

### `setup_deployed_tests.py`
Setup script for preparing deployed environment tests.

**Usage:**
```bash
uv run scripts/setup_deployed_tests.py
```

**What it does:**
- Configures test environment variables
- Creates necessary test data
- Sets up external service mocks
- Prepares for E2E testing in production-like environment

**Configuration:**
```python
# Customizable via environment variables
DEPLOYED_SERVICE_URL = "https://your-service.com"
TEST_USER_ID = "e2e-test-user"
TEST_PROJECT_KEY = "TEST"
```

## Common Tasks

### Running All Scripts
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run deployment
./scripts/deploy.sh

# Generate test tokens
uv run scripts/generate_e2e_tokens.py

# Setup deployed tests
uv run scripts/setup_deployed_tests.py
```

### Testing Tokens Generated
```bash
# Check generated tokens
sqlite3 test_tokens.db "SELECT * FROM tokens LIMIT 5;"
```

### Cleaning Up
```bash
# Remove generated test databases
rm -f test_tokens.db jira_tokens.db

# Remove Docker images
docker rmi $(docker images | grep ticket-service | awk '{print $3}')
```

## Development Workflow

### Local Development
1. Generate local test tokens: `uv run scripts/generate_e2e_tokens.py`
2. Start service: `uv run uvicorn src.ticket_service.main:app --reload`
3. Run tests: `uv run pytest tests/`

### Staging Deployment
1. Fix packages: `./scripts/fix_slack_packages.sh`
2. Deploy: `DEPLOY_ENV=staging ./scripts/deploy.sh`
3. Setup tests: `uv run scripts/setup_deployed_tests.py`

### Production Deployment
1. Verify all tests pass locally
2. Deploy: `DEPLOY_ENV=prod ./scripts/deploy.sh`
3. Monitor metrics: Check `/metrics` endpoint

## Troubleshooting

### Token Generation Fails
```bash
# Check Jira OAuth credentials
echo $OAUTH_CLIENT_ID
echo $OAUTH_CLIENT_SECRET

# Test OAuth endpoint
curl https://auth.atlassian.com/oauth/token
```

### Deploy Script Fails
```bash
# Check Docker daemon
docker ps

# Verify registry credentials
docker login

# Check environment variables
env | grep DEPLOY
```

### Slack Package Issues
```bash
# Run fix script again
./scripts/fix_slack_packages.sh

# Check package versions
pip list | grep slack
```

## Integration with CI/CD

These scripts are used in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Generate test tokens
  run: uv run scripts/generate_e2e_tokens.py

- name: Deploy
  if: github.ref == 'refs/heads/main'
  run: DEPLOY_ENV=prod ./scripts/deploy.sh

- name: Setup deployed tests
  if: github.ref == 'refs/heads/main'
  run: uv run scripts/setup_deployed_tests.py
```

## Further Reading

- [Deployment Guide](../../DEPLOYMENT.md)
- [Testing Documentation](../../docs/testing.md)
- [Architecture Design](../../DESIGN.md)
