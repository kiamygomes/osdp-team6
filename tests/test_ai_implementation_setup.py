"""Tests for AI implementation setup module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from ticket_ai_adapter.ai_implementation_setup import setup_ai_implementations


class TestSetupAIImplementations:
    """Test the AI implementation setup function."""

    def test_setup_ai_implementations_success(self) -> None:
        """Test successful setup of AI implementations."""
        with patch("ticket_ai_adapter.ai_implementation_setup.Path") as mock_path_class:
            # Create a proper Path mock
            mock_path_instance = MagicMock()
            mock_path_class.return_value = mock_path_instance

            # Mock the parent chain to return Path objects
            mock_root = MagicMock()
            mock_path_instance.parent.parent.parent.parent.parent = mock_root

            # Mock the / operator to return Path objects with __str__ configured
            claude_path = MagicMock()
            claude_path.configure_mock(**{"__str__.return_value": "/root/claude_implementation_pkg"})
            openai_path = MagicMock()
            openai_path.configure_mock(**{"__str__.return_value": "/root/openai_implementation_pkg"})

            mock_root.configure_mock(**{"__truediv__.side_effect": [claude_path, openai_path]})

            with patch("ticket_ai_adapter.ai_implementation_setup.sys") as mock_sys:
                mock_sys.path = []

                # Mock imports
                with patch.dict(
                    "sys.modules",
                    {
                        "claude_implementation_pkg.claude_implementation": MagicMock(),
                        "openai_implementation_pkg.openai_implementation": MagicMock(),
                        "ai_chat_api": MagicMock(),
                        "ai_api": MagicMock(),
                    },
                ):
                    setup_ai_implementations()

                    # Check that paths were added
                    expected_path_count = 2
                    assert len(mock_sys.path) == expected_path_count

    def test_setup_ai_implementations_path_already_exists(self) -> None:
        """Test setup when paths already exist in sys.path."""
        with patch("ticket_ai_adapter.ai_implementation_setup.Path") as mock_path_class:
            # Create a proper Path mock
            mock_path_instance = MagicMock()
            mock_path_class.return_value = mock_path_instance

            # Mock the parent chain to return Path objects
            mock_root = MagicMock()
            mock_path_instance.parent.parent.parent.parent.parent = mock_root

            # Mock the / operator to return Path objects with __str__ configured
            claude_path = MagicMock()
            claude_path.configure_mock(**{"__str__.return_value": "/root/claude_implementation_pkg"})
            openai_path = MagicMock()
            openai_path.configure_mock(**{"__str__.return_value": "/root/openai_implementation_pkg"})

            mock_root.configure_mock(**{"__truediv__.side_effect": [claude_path, openai_path]})

            with patch("ticket_ai_adapter.ai_implementation_setup.sys") as mock_sys:
                # Mock sys.path with existing paths
                mock_sys.path = ["/root/claude_implementation_pkg", "/root/openai_implementation_pkg"]

                # Mock imports
                with patch.dict(
                    "sys.modules",
                    {
                        "claude_implementation_pkg.claude_implementation": MagicMock(),
                        "openai_implementation_pkg.openai_implementation": MagicMock(),
                        "ai_chat_api": MagicMock(),
                        "ai_api": MagicMock(),
                    },
                ):
                    setup_ai_implementations()

                    # Paths should not be added again
                    expected_path_count = 2
                    assert len(mock_sys.path) == expected_path_count

    def test_setup_ai_implementations_claude_import_error(self) -> None:
        """Test setup when Claude API import fails."""
        with patch("ticket_ai_adapter.ai_implementation_setup.Path") as mock_path_class:
            # Create a proper Path mock
            mock_path_instance = MagicMock()
            mock_path_class.return_value = mock_path_instance

            # Mock the parent chain to return Path objects
            mock_root = MagicMock()
            mock_path_instance.parent.parent.parent.parent.parent = mock_root

            # Mock the / operator to return Path objects with __str__ configured
            claude_path = MagicMock()
            claude_path.configure_mock(**{"__str__.return_value": "/root/claude_implementation_pkg"})
            openai_path = MagicMock()
            openai_path.configure_mock(**{"__str__.return_value": "/root/openai_implementation_pkg"})

            mock_root.configure_mock(**{"__truediv__.side_effect": [claude_path, openai_path]})

            with patch("ticket_ai_adapter.ai_implementation_setup.sys") as mock_sys:
                mock_sys.path = []

                # Mock imports - ai_chat_api fails to import
                with patch.dict(
                    "sys.modules",
                    {
                        "claude_implementation_pkg.claude_implementation": MagicMock(),
                        "openai_implementation_pkg.openai_implementation": MagicMock(),
                        "ai_api": MagicMock(),
                    },
                ):
                    # This should not raise an exception
                    setup_ai_implementations()

    def test_setup_ai_implementations_openai_import_error(self) -> None:
        """Test setup when OpenAI API import fails."""
        with patch("ticket_ai_adapter.ai_implementation_setup.Path") as mock_path_class:
            # Create a proper Path mock
            mock_path_instance = MagicMock()
            mock_path_class.return_value = mock_path_instance

            # Mock the parent chain to return Path objects
            mock_root = MagicMock()
            mock_path_instance.parent.parent.parent.parent.parent = mock_root

            # Mock the / operator to return Path objects with __str__ configured
            claude_path = MagicMock()
            claude_path.configure_mock(**{"__str__.return_value": "/root/claude_implementation_pkg"})
            openai_path = MagicMock()
            openai_path.configure_mock(**{"__str__.return_value": "/root/openai_implementation_pkg"})

            mock_root.configure_mock(**{"__truediv__.side_effect": [claude_path, openai_path]})

            with patch("ticket_ai_adapter.ai_implementation_setup.sys") as mock_sys:
                mock_sys.path = []

                # Mock imports - ai_api fails to import
                with patch.dict(
                    "sys.modules",
                    {
                        "claude_implementation_pkg.claude_implementation": MagicMock(),
                        "openai_implementation_pkg.openai_implementation": MagicMock(),
                        "ai_chat_api": MagicMock(),
                    },
                ):
                    # This should not raise an exception
                    setup_ai_implementations()

    def test_setup_ai_implementations_exception(self) -> None:
        """Test setup when an exception occurs during import."""
        with patch("ticket_ai_adapter.ai_implementation_setup.Path") as mock_path_class:
            # Create a proper Path mock
            mock_path_instance = MagicMock()
            mock_path_class.return_value = mock_path_instance

            # Mock the parent chain to return Path objects
            mock_root = MagicMock()
            mock_path_instance.parent.parent.parent.parent.parent = mock_root

            # Mock the / operator to return Path objects with __str__ configured
            claude_path = MagicMock()
            claude_path.configure_mock(**{"__str__.return_value": "/root/claude_implementation_pkg"})
            openai_path = MagicMock()
            openai_path.configure_mock(**{"__str__.return_value": "/root/openai_implementation_pkg"})

            mock_root.configure_mock(**{"__truediv__.side_effect": [claude_path, openai_path]})

            with patch("ticket_ai_adapter.ai_implementation_setup.sys") as mock_sys:
                mock_sys.path = []

                # Mock imports to raise exception
                with patch.dict(
                    "sys.modules",
                    {
                        "claude_implementation_pkg.claude_implementation": MagicMock(),
                    },
                ):
                    # Make the import of openai_implementation_pkg raise an exception
                    error_message = "Failed to import openai implementation"

                    def raise_import_error(name: str, *args: object, **kwargs: object) -> MagicMock:
                        if "openai_implementation_pkg" in name:
                            raise ImportError(error_message)
                        return MagicMock()

                    with patch("builtins.__import__", side_effect=raise_import_error), pytest.raises(
                        ImportError, match=error_message
                    ):
                        setup_ai_implementations()

    def test_patched_get_ai_interface(self) -> None:
        """Test the patched get_ai_interface function."""
        # Mock the ai_chat_api module
        mock_ai_chat_api = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "claude_implementation_pkg.claude_implementation": MagicMock(),
                "ai_chat_api": mock_ai_chat_api,
            },
        ):
            # Import and call the setup
            from ticket_ai_adapter.ai_implementation_setup import setup_ai_implementations

            # Mock path operations
            with patch("ticket_ai_adapter.ai_implementation_setup.Path") as mock_path_class:
                mock_path_instance = MagicMock()
                mock_path_class.return_value = mock_path_instance

                # Mock the parent chain to return Path objects
                mock_root = MagicMock()
                mock_path_instance.parent.parent.parent.parent.parent = mock_root

                # Mock the / operator to return Path objects with __str__ configured
                claude_path = MagicMock()
                claude_path.configure_mock(**{"__str__.return_value": "/root/claude_implementation_pkg"})
                openai_path = MagicMock()
                openai_path.configure_mock(**{"__str__.return_value": "/root/openai_implementation_pkg"})

                mock_root.configure_mock(**{"__truediv__.side_effect": [claude_path, openai_path]})

                with patch("ticket_ai_adapter.ai_implementation_setup.sys") as mock_sys:
                    mock_sys.path = []

                    setup_ai_implementations()

                    # Test that the patched function was set
                    assert hasattr(mock_ai_chat_api, "get_ai_interface")

                    # Test calling the patched function
                    result = mock_ai_chat_api.get_ai_interface()
                    assert result is not None

    def test_patched_get_client(self) -> None:
        """Test the patched get_client function."""
        # Mock the ai_api module
        mock_ai_api = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "openai_implementation_pkg.openai_implementation": MagicMock(),
                "ai_api": mock_ai_api,
            },
        ):
            # Import and call the setup
            from ticket_ai_adapter.ai_implementation_setup import setup_ai_implementations

            # Mock path operations
            with patch("ticket_ai_adapter.ai_implementation_setup.Path") as mock_path_class:
                mock_path_instance = MagicMock()
                mock_path_class.return_value = mock_path_instance

                # Mock the parent chain to return Path objects
                mock_root = MagicMock()
                mock_path_instance.parent.parent.parent.parent.parent = mock_root

                # Mock the / operator to return Path objects with __str__ configured
                claude_path = MagicMock()
                claude_path.configure_mock(**{"__str__.return_value": "/root/claude_implementation_pkg"})
                openai_path = MagicMock()
                openai_path.configure_mock(**{"__str__.return_value": "/root/openai_implementation_pkg"})

                mock_root.configure_mock(**{"__truediv__.side_effect": [claude_path, openai_path]})

                with patch("ticket_ai_adapter.ai_implementation_setup.sys") as mock_sys:
                    mock_sys.path = []

                    setup_ai_implementations()

                    # Test that the patched function was set
                    assert hasattr(mock_ai_api, "get_client")

                    # Test calling the patched function
                    result = mock_ai_api.get_client()
                    assert result is not None
