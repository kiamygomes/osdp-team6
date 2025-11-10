#!/usr/bin/env python3
"""Generate OAuth tokens for e2e testing.

This script exchanges an OAuth authorization code for access/refresh tokens
and stores them in the database for demo_user. This is used in CI/CD to set up
e2e test credentials without requiring manual OAuth flow interaction.

Usage:
    # Using authorization code
    python scripts/generate_e2e_tokens.py --code <authorization_code>

    # Using existing access/refresh tokens (for CI/CD)
    python scripts/generate_e2e_tokens.py --tokens <access_token> <refresh_token>

The following environment variables must be set:
    - OAUTH_CLIENT_ID
    - OAUTH_CLIENT_SECRET
    - OAUTH_REDIRECT_URI
    - JIRA_CLOUD_ID
    - DB_URL (optional, defaults to sqlite:///./jira_tokens.db)
"""

import asyncio
import logging
import sys
from pathlib import Path

if __name__ == "__main__":
    # Add src directories to Python path before any imports
    _script_dir = Path(__file__).parent
    sys.path.insert(0, str(_script_dir.parent / "src" / "ticket_impl" / "src"))
    sys.path.insert(0, str(_script_dir.parent / "src" / "ticket_api" / "src"))
    sys.path.insert(0, str(_script_dir.parent / "src" / "ticket_service" / "src"))

    import ticket_impl.config
    import ticket_impl.oauth
    import ticket_impl.storage

# Constants
MIN_ARGS = 2
CODE_ARGS_COUNT = 3
TOKENS_MIN_ARGS = 4
TOKENS_MAX_ARG_INDEX = 4
TOKEN_PREVIEW_LENGTH = 20
DEFAULT_EXPIRES_SEC = 3600

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def print_usage() -> None:
    """Print usage instructions."""
    usage_text = (
        "Usage:\n"
        "  python generate_e2e_tokens.py --code <authorization_code>\n"
        "  python generate_e2e_tokens.py --tokens <access_token> <refresh_token> [expires_in_sec]\n"
        "\nEnvironment variables required:\n"
        "  - OAUTH_CLIENT_ID\n"
        "  - OAUTH_CLIENT_SECRET\n"
        "  - OAUTH_REDIRECT_URI\n"
        "  - JIRA_CLOUD_ID"
    )
    logger.error(usage_text)


async def main() -> None:
    """Generate and store OAuth tokens for demo_user."""
    if len(sys.argv) < MIN_ARGS:
        print_usage()
        sys.exit(1)

    # Verify required settings
    required_settings = [
        ("oauth_client_id", ticket_impl.config.settings.oauth_client_id),
        ("oauth_client_secret", ticket_impl.config.settings.oauth_client_secret),
        ("oauth_redirect_uri", ticket_impl.config.settings.oauth_redirect_uri),
        ("jira_cloud_id", ticket_impl.config.settings.jira_cloud_id),
    ]

    missing = [name for name, value in required_settings if not value or value.startswith("dummy")]
    if missing:
        logger.error("Error: Missing or invalid settings: %s", ", ".join(missing))
        logger.error("Please ensure all OAuth credentials are configured.")
        sys.exit(1)

    try:
        code_mode = sys.argv[1] == "--code"
        tokens_mode = sys.argv[1] == "--tokens"
        code_args_valid = code_mode and len(sys.argv) == CODE_ARGS_COUNT
        tokens_args_valid = tokens_mode and len(sys.argv) >= TOKENS_MIN_ARGS

        if code_args_valid:
            # Exchange authorization code for tokens
            auth_code = sys.argv[2]
            logger.info("Exchanging authorization code for tokens...")
            access_token, refresh_token, expires_in = await ticket_impl.oauth.exchange_code_for_tokens(
                "demo_user",
                auth_code,
            )
            logger.info("✓ Successfully generated tokens for demo_user")
            logger.info("  Access token: %s...", access_token[:TOKEN_PREVIEW_LENGTH])
            logger.info("  Refresh token: %s...", refresh_token[:TOKEN_PREVIEW_LENGTH])
            logger.info("  Expires in: %d seconds", expires_in)

        elif tokens_args_valid:
            # Directly insert tokens (for CI/CD with existing tokens)
            access_token = sys.argv[2]
            refresh_token = sys.argv[3]
            expires_in_sec = (
                int(sys.argv[TOKENS_MAX_ARG_INDEX])
                if len(sys.argv) > TOKENS_MAX_ARG_INDEX
                else DEFAULT_EXPIRES_SEC
            )

            logger.info("Storing tokens for demo_user...")
            ticket_impl.storage.upsert_tokens("demo_user", access_token, refresh_token, expires_in_sec)
            logger.info("✓ Successfully stored tokens for demo_user")
            logger.info("  Access token: %s...", access_token[:TOKEN_PREVIEW_LENGTH])
            logger.info("  Refresh token: %s...", refresh_token[:TOKEN_PREVIEW_LENGTH])
            logger.info("  Expires in: %d seconds", expires_in_sec)

        else:
            logger.error("Error: Invalid arguments")
            print_usage()
            sys.exit(1)

    except (RuntimeError, ValueError):
        logger.exception("Error occurred")


if __name__ == "__main__":
    asyncio.run(main())
