# Mail Client Service

## Overview
The `mail_client_service` package provides a FastAPI web service that exposes mail operations through REST endpoints. It acts as an HTTP wrapper around the Mail Client API, allowing remote access to mail functionality.

## Files

### main.py
Contains the FastAPI application with mail-related endpoints that handle HTTP requests and responses.

#### FastAPI App
Creates the web application with metadata for API documentation.
```python
app = FastAPI(
    title="Mail Client API Service",
    description="A thin wrapper around the mail client implementation (GmailClient).",
    version="1.0.0",
)
```

#### Router
Defines the URL prefix for all mail-related endpoints.
```python
router = APIRouter(prefix="/messages")
```

#### Dependencies
Dependency injection functions for providing mail client instances to endpoints.

##### get_mail_client() -> Client
Returns a configured mail client instance for endpoint dependency injection.

**Returns:**
- `Client`: Configured mail client instance

**Raises:**
- `HTTPException`: Status 503 when mail client initialization fails due to RuntimeError

##### MailClientDep
Type alias `Annotated[Client, Depends(get_mail_client)]` for cleaner endpoint signatures.

#### Models (in main.py)
Simple Pydantic models for request/response serialization.
```python
class MessageSummary(BaseModel):
    """Basic message information for list responses."""
    id: str
    from_: str | None = None
    subject: str | None = None
    date: str | None = None

class MessageDetail(BaseModel):
    """Complete message information including body."""
    id: str
    from_: str
    to: str
    date: str
    subject: str
    body: str
```

#### Endpoints
REST API endpoints that map HTTP operations to mail client methods.

##### get_messages_summary(client: MailClientDep, max_results: int = 10) -> list[MessageSummary]
**GET /messages** - Fetches a list of message summaries.

**Parameters:**
- `client` (MailClientDep): Injected mail client instance
- `max_results` (int, optional): Maximum number of messages to return. Default: 10

**Returns:**
- `list[MessageSummary]`: List of message summary objects

**Raises:**
- `HTTPException`: Status 500 when message fetching fails

##### get_message_detail(message_id: str, client: MailClientDep) -> MessageDetail
**GET /messages/{message_id}** - Fetches full details of a single message.

**Parameters:**
- `message_id` (str): Unique identifier of the message
- `client` (MailClientDep): Injected mail client instance

**Returns:**
- `MessageDetail`: Complete message details including body

**Raises:**
- `HTTPException`: Status 404 when message not found or inaccessible

##### mark_message_as_read(message_id: str, client: MailClientDep) -> JSONResponse
**POST /messages/{message_id}/mark-as-read** - Marks a message as read.

**Parameters:**
- `message_id` (str): Unique identifier of the message
- `client` (MailClientDep): Injected mail client instance

**Returns:**
- `JSONResponse`: Success message with status 200

**Raises:**
- `HTTPException`: Status 500 when mark-as-read operation fails

##### delete_message(message_id: str, client: MailClientDep) -> JSONResponse
**DELETE /messages/{message_id}** - Deletes a message.

**Parameters:**
- `message_id` (str): Unique identifier of the message
- `client` (MailClientDep): Injected mail client instance

**Returns:**
- `JSONResponse`: Success message with status 200

**Raises:**
- `HTTPException`: Status 500 when delete operation fails

### models.py
Contains enhanced Pydantic models with detailed field descriptions and validation for API documentation.

#### MessageSummary
Enhanced version with field descriptions and JSON alias support for the `from` field.
```python
class MessageSummary(BaseModel):
    id: str = Field(..., description="Unique message identifier")
    from_: str = Field(..., alias="from", description="Sender email address")
    to: str = Field(..., description="Recipient email address")
    date: str = Field(..., description="Message date")
    subject: str = Field(..., description="Message subject")

    class Config:
        populate_by_name = True  # Allows both 'from_' and 'from' in JSON
```

#### MessageDetail
Enhanced version with field descriptions and JSON alias support.
```python
class MessageDetail(BaseModel):
    id: str = Field(..., description="Unique message identifier")
    from_: str = Field(..., alias="from", description="Sender email address")
    to: str = Field(..., description="Recipient email address")
    date: str = Field(..., description="Message date")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message body content")

    class Config:
        populate_by_name = True  # Allows both 'from_' and 'from' in JSON
```

#### MessageListResponse
Response wrapper for message list endpoints (not used in main.py).
```python
class MessageListResponse(BaseModel):
    messages: list[MessageSummary] = Field(..., description="List of message summaries")
    count: int = Field(..., description="Number of messages returned")
```

#### SuccessResponse
Generic success response model (not used in main.py).
```python
class SuccessResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")
```

#### ErrorResponse
Error response model (not used in main.py).
```python
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")
```

## Imports

### main.py
- `import logging`
- `from typing import Annotated`
- `from fastapi import APIRouter, Depends, FastAPI, HTTPException`
- `from fastapi.responses import JSONResponse`
- `from pydantic import BaseModel`
- `from mail_client_api import Client, get_client`

### models.py
- `from pydantic import BaseModel, Field`