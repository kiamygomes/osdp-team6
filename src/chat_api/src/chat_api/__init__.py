"""Chat API - Shared interface for Chat services.

This module provides the standardized interface for chat integration
as defined in the OSS-APIs repository.
"""

from .shared_interface import ChatInterface, Message

__all__ = ["ChatInterface", "Message"]
