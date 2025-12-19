"""Setup module to inject AI implementations into external team packages.

This module provides a workaround for the fact that we cannot push commits to
the external team repositories. Instead of modifying their code, we dynamically
inject our implementations at runtime.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_ai_implementations() -> None:
    """Inject AI implementations into external team packages.

    This function:
    1. Adds our implementation packages to sys.modules
    2. Monkey-patches the get_client() and get_ai_interface() functions
       in the external packages to return our implementations
    """
    # Import our implementations
    try:
        # Add the implementation package paths to Python path
        implementations_root = Path(__file__).parent.parent.parent.parent.parent
        claude_impl_path = implementations_root / "claude_implementation_pkg"
        openai_impl_path = implementations_root / "openai_implementation_pkg"

        # Add to sys.path if not already there
        for path in [claude_impl_path, openai_impl_path]:
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)

        # Now import our implementations (dynamically added to sys.path above)
        from claude_implementation_pkg.claude_implementation import (
            ClaudeAIClient,  # type: ignore[import-not-found]
        )
        from openai_implementation_pkg.openai_implementation import (
            OpenAIClient,  # type: ignore[import-not-found]
        )

        # Monkey-patch the external packages
        try:
            import ai_chat_api

            def patched_get_ai_interface() -> ClaudeAIClient:
                """Return our Claude implementation."""
                logger.info("Using injected Claude AI implementation")
                return ClaudeAIClient()

            ai_chat_api.get_ai_interface = patched_get_ai_interface
            logger.info("Successfully patched ai_chat_api.get_ai_interface")
        except ImportError:
            logger.warning("Could not import ai_chat_api - Claude integration may not work")

        try:
            import ai_api

            def patched_get_client() -> OpenAIClient:
                """Return our OpenAI implementation."""
                logger.info("Using injected OpenAI implementation")
                return OpenAIClient()

            ai_api.get_client = patched_get_client
            logger.info("Successfully patched ai_api.get_client")
        except ImportError:
            logger.warning("Could not import ai_api - OpenAI integration may not work")

    except Exception:
        logger.exception("Failed to setup AI implementations")
        raise
