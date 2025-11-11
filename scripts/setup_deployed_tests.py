#!/usr/bin/env python3
"""Setup script to get the correct user ID for deployed e2e tests.

This script helps you:
1. Find out what user ID has valid tokens on the deployed service
2. Update your .env file with the correct user ID
"""

import sys
from pathlib import Path

import httpx


def main() -> None:
    """Check deployed service and guide user to set up tests."""
    base_url = "https://osdp-team6.onrender.com"

    print(" Checking deployed service authentication...\n")

    # Try to get auth status
    try:
        response = httpx.get(f"{base_url}/api/v1/auth/status", timeout=10.0)
        data = response.json()

        if data.get("authenticated"):
            user_id = data.get("user_id")
            print(" Found authenticated session!")
            print(f"   User ID: {user_id}\n")

            # Update .env file
            env_path = Path(".env")
            if env_path.exists():
                content = env_path.read_text()
                if f'OAUTH_USER_ID="{user_id}"' in content:
                    print("Your .env file already has the correct user ID!")
                else:
                    # Update the OAUTH_USER_ID line
                    lines = content.split("\n")
                    updated = False
                    for i, line in enumerate(lines):
                        if line.startswith("OAUTH_USER_ID="):
                            lines[i] = f'OAUTH_USER_ID="{user_id}"'
                            updated = True
                            break

                    if updated:
                        env_path.write_text("\n".join(lines))
                        print(f'Updated .env with OAUTH_USER_ID="{user_id}"')
                    else:
                        print("\n  Please add this to your .env file:")
                        print(f'   OAUTH_USER_ID="{user_id}"')
            else:
                print("\n  Please create a .env file with:")
                print(f'   OAUTH_USER_ID="{user_id}"')

            print("\n You're ready to run deployed tests:")
            print("   uv run pytest tests/e2e/test_e2e_deployed.py -v --no-cov\n")

        else:
            print(" No authenticated session found on deployed service.\n")
            print(" To set up authentication:")
            print(f"   1. Open: {base_url}/api/v1/auth/login")
            print("   2. Complete the Jira OAuth flow")
            print("   3. Run this script again\n")
            sys.exit(1)

    except httpx.RequestError as e:
        print(f" Could not connect to deployed service: {e}\n")
        print(f"   Make sure {base_url} is accessible")
        sys.exit(1)


if __name__ == "__main__":
    main()
