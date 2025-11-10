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
import os
import sys
from datetime import UTC, datetime, timedelta

# Ensure we can import from src directories
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ticket_impl", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ticket_api", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ticket_service", "src"))

from ticket_impl.config import settings  # noqa: E402
from ticket_impl.oauth import exchange_code_for_tokens  # noqa: E402
from ticket_impl.storage import upsert_tokens  # noqa: E402


async def main() -> None:
    """Generate and store OAuth tokens for demo_user."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_e2e_tokens.py --code <authorization_code>")
        print("  python generate_e2e_tokens.py --tokens <access_token> <refresh_token> [expires_in_sec]")
        print("\nEnvironment variables required:")
        print("  - OAUTH_CLIENT_ID")
        print("  - OAUTH_CLIENT_SECRET")
        print("  - OAUTH_REDIRECT_URI")
        print("  - JIRA_CLOUD_ID")
        sys.exit(1)

    # Verify required settings
    required_settings = [
        ("oauth_client_id", settings.oauth_client_id),
        ("oauth_client_secret", settings.oauth_client_secret),
        ("oauth_redirect_uri", settings.oauth_redirect_uri),
        ("jira_cloud_id", settings.jira_cloud_id),
    ]

    missing = [name for name, value in required_settings if not value or value.startswith("dummy")]
    if missing:
        print(f"Error: Missing or invalid settings: {', '.join(missing)}", file=sys.stderr)
        print("Please ensure all OAuth credentials are configured.", file=sys.stderr)
        sys.exit(1)

    try:
        if sys.argv[1] == "--code" and len(sys.argv) == 3:
            # Exchange authorization code for tokens
            auth_code = sys.argv[2]
            print(f"Exchanging authorization code for tokens...")
            access_token, refresh_token, expires_in = await exchange_code_for_tokens(
                "demo_user", auth_code
            )
            print(f"✓ Successfully generated tokens for demo_user")
            print(f"  Access token: {access_token[:20]}...")
            print(f"  Refresh token: {refresh_token[:20]}...")
            print(f"  Expires in: {expires_in} seconds")

        elif sys.argv[1] == "--tokens" and len(sys.argv) >= 4:
            # Directly insert tokens (for CI/CD with existing tokens)
            access_token = sys.argv[2]
            refresh_token = sys.argv[3]
            expires_in_sec = int(sys.argv[4]) if len(sys.argv) > 4 else 3600

            print(f"Storing tokens for demo_user...")
            upsert_tokens("demo_user", access_token, refresh_token, expires_in_sec)
            print(f"✓ Successfully stored tokens for demo_user")
            print(f"  Access token: {access_token[:20]}...")
            print(f"  Refresh token: {refresh_token[:20]}...")
            print(f"  Expires in: {expires_in_sec} seconds")

        else:
            print("Error: Invalid arguments", file=sys.stderr)
            print("\nUsage:")
            print("  python generate_e2e_tokens.py --code <authorization_code>")
            print("  python generate_e2e_tokens.py --tokens <access_token> <refresh_token> [expires_in_sec]")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
