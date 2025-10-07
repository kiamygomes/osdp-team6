import logging
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mail_client_api import Client, get_client

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Mail Client API Service",
    description="A thin wrapper around the mail client implementation (GmailClient).",
    version="1.0.0",
)
router = APIRouter(prefix="/messages")


def get_mail_client() -> Client:
    """Dependency that yields a configured mail client instance."""
    try:
        # The API contract is fulfilled by the concrete implementation (e.g., GmailClient or Adapter)
        client = get_client(interactive=False)
        return client
    except RuntimeError as e:
        logger.error("Failed to initialize mail client: %s", e)
        raise HTTPException(
            status_code=503,
            detail=f"Service initialization failed. Authentication error: {e}",
        ) from e


# Alias for type hinting in endpoints
MailClientDep = Annotated[Client, Depends(get_mail_client)]


# --- Models (Updated to reflect API contract attributes) ---


class MessageSummary(BaseModel):
    """A summary of a message containing only essential information."""

    id: str
    from_: str | None = None  # Renamed to match the client's 'from_' attribute
    subject: str | None = None
    date: str | None = None  # Added date


class MessageDetail(BaseModel):
    """Complete message details."""

    id: str
    from_: str
    to: str
    date: str
    subject: str
    body: str


# Class ActionResult removed as it wasn't used in the original provided code.


@router.get("", response_model=list[MessageSummary])
def get_messages_summary(client: MailClientDep, max_results: int = 10) -> list[MessageSummary]:
    """Fetches a list of message summaries."""
    try:
        # Refactor: Use Pydantic's automatic dictionary mapping via a comprehension
        # The 'msg.dict()' or 'MessageSummary(**msg.dict())' approach is cleaner,
        # but the simplest way is to iterate and pass keyword arguments.

        return [
            MessageSummary(
                id=msg.id,
                from_=msg.from_,  # Uses the client's attribute name
                subject=msg.subject,
                date=msg.date,
            )
            for msg in client.get_messages(max_results=max_results)
        ]
    except Exception as e:
        logger.error("Error fetching messages: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {e}")


@router.get("/{message_id}", response_model=MessageDetail)
def get_message_detail(message_id: str, client: MailClientDep) -> MessageDetail:
    """Fetches the full detail of a single message."""
    try:
        msg = client.get_message(message_id)

        # Refactor: Instantiate the Pydantic model directly
        return MessageDetail(
            id=msg.id,
            from_=msg.from_,
            to=msg.to,
            date=msg.date,
            subject=msg.subject,
            body=msg.body,
        )
    except Exception as e:
        # Assuming any failure to fetch means the message is Not Found for simplicity here
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found or inaccessible: {e}")


@router.post("/{message_id}/mark-as-read", status_code=200)
def mark_message_as_read(message_id: str, client: MailClientDep) -> JSONResponse:
    """Marks a message as read."""
    if client.mark_as_read(message_id):
        # Returns a standard JSON response on success
        return JSONResponse(status_code=200, content={"message": f"Message {message_id} marked as read."})

    raise HTTPException(status_code=500, detail=f"Failed to mark message {message_id} as read.")


@router.delete("/{message_id}", status_code=200)
def delete_message(message_id: str, client: MailClientDep) -> JSONResponse:
    """Deletes a message."""
    if client.delete_message(message_id):
        return JSONResponse(status_code=200, content={"message": f"Message {message_id} deleted."})

    raise HTTPException(status_code=500, detail=f"Failed to delete message {message_id}.")


app.include_router(router)
