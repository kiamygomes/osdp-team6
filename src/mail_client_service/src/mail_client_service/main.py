"""Mail Client API Service.

This module implements a FastAPI application that wraps a mail client
implementation (GmailClient) to expose message listing, retrieval,
mark-as-read, and delete operations.

Exports:
- FastAPI `app` with routes under /messages.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response
from gmail_client_impl import register
from mail_client_api import Client, get_client

from .constants import (
    ERROR_AUTH_FAILED,
    ERROR_DELETE_FAILED,
    ERROR_FETCH_MESSAGE_FAILED,
    ERROR_FETCH_MESSAGES_FAILED,
    ERROR_MARK_READ_FAILED,
    ERROR_MESSAGE_NOT_FOUND,
    ERROR_RATE_LIMIT,
    ERROR_SERVICE_INIT_FAILED,
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)
from .models import MessageDetail, MessageSummary

logger = logging.getLogger(__name__)

register()


app = FastAPI(
    title="Mail Client API Service",
    description="A thin wrapper around the mail client implementation (GmailClient).",
    version="1.0.0",
)
router = APIRouter(prefix="/messages")


# Custom exception classes for precise error mapping
class NotFoundError(Exception):
    """Raised when a resource is not found."""


class AuthError(Exception):
    """Raised when authentication fails."""


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""


def get_mail_client() -> Client:
    """Dependency that yields a configured mail client instance."""
    try:
        return get_client(interactive=False)
    except RuntimeError as e:
        logger.exception("Failed to initialize mail client")
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=ERROR_SERVICE_INIT_FAILED,
        ) from e


# Alias for type hinting in endpoints
MailClientDep = Annotated[Client, Depends(get_mail_client)]


@router.get("", status_code=HTTP_200_OK)
def get_messages_summary(client: MailClientDep, max_results: int = 10) -> list[MessageSummary]:
    """Return a list of message summaries."""
    try:
        return [
            MessageSummary(
                id=msg.id,
                **{"from": msg.from_},
                to=msg.to,
                subject=msg.subject,
                date=msg.date,
            )
            for msg in client.get_messages(max_results=max_results)
        ]
    except RateLimitError as e:
        logger.exception("Rate limit exceeded while fetching messages")
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=ERROR_RATE_LIMIT,
        ) from e
    except AuthError as e:
        logger.exception("Authentication error while fetching messages")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=ERROR_AUTH_FAILED,
        ) from e
    except Exception as e:
        logger.exception("Unexpected error fetching messages")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_FETCH_MESSAGES_FAILED,
        ) from e


@router.get("/{message_id}", status_code=HTTP_200_OK)
def get_message_detail(message_id: str, client: MailClientDep) -> MessageDetail:
    """Fetch the full detail of a single message."""
    try:
        msg = client.get_message(message_id)
        return MessageDetail(
            id=msg.id,
            **{"from": msg.from_},
            to=msg.to,
            date=msg.date,
            subject=msg.subject,
            body=msg.body,
        )
    except NotFoundError as e:
        logger.exception("Message not found: %s", message_id)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGE_NOT_FOUND,
        ) from e
    except AuthError as e:
        logger.exception("Authentication error while fetching message: %s", message_id)
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=ERROR_AUTH_FAILED,
        ) from e
    except RateLimitError as e:
        logger.exception("Rate limit exceeded while fetching message: %s", message_id)
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=ERROR_RATE_LIMIT,
        ) from e
    except Exception as e:
        logger.exception("Unexpected error fetching message: %s", message_id)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_FETCH_MESSAGE_FAILED,
        ) from e


@router.post("/{message_id}/mark-as-read", status_code=HTTP_204_NO_CONTENT)
def mark_message_as_read(message_id: str, client: MailClientDep) -> Response:
    """Mark a message as read."""

    def _raise_mark_read_failed() -> None:
        """Raise the HTTPException for a mark-as-read failure."""
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MARK_READ_FAILED,
        )

    try:
        if not client.mark_as_read(message_id):
            logger.error("Failed to mark message as read: %s", message_id)
            _raise_mark_read_failed()
        return Response(status_code=HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        logger.exception("Message not found: %s", message_id)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGE_NOT_FOUND,
        ) from e
    except AuthError as e:
        logger.exception("Authentication error while marking message as read: %s", message_id)
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=ERROR_AUTH_FAILED,
        ) from e
    except RateLimitError as e:
        logger.exception("Rate limit exceeded while marking message as read: %s", message_id)
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=ERROR_RATE_LIMIT,
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error marking message as read: %s", message_id)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MARK_READ_FAILED,
        ) from e


@router.delete("/{message_id}", status_code=HTTP_204_NO_CONTENT)
def delete_message(message_id: str, client: MailClientDep) -> Response:
    """Delete a message."""

    def _raise_delete_failed() -> None:
        """Raise the HTTPException for a delete failure."""
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_DELETE_FAILED,
        )

    try:
        if not client.delete_message(message_id):
            logger.error("Failed to delete message: %s", message_id)
            _raise_delete_failed()

        return Response(status_code=HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        logger.exception("Message not found: %s", message_id)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGE_NOT_FOUND,
        ) from e
    except AuthError as e:
        logger.exception("Authentication error while deleting message: %s", message_id)
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=ERROR_AUTH_FAILED,
        ) from e
    except RateLimitError as e:
        logger.exception("Rate limit exceeded while deleting message: %s", message_id)
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=ERROR_RATE_LIMIT,
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error deleting message: %s", message_id)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_DELETE_FAILED,
        ) from e


app.include_router(router)
