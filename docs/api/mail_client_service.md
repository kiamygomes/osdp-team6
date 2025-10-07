# Mail Client Service Reference

The `mail_client_service` package provides a FastAPI web service that exposes mail operations through REST endpoints.

## main.py

### FastAPI Application
Creates the main web application with metadata for automatic API documentation.
```python
app = FastAPI(
    title="Mail Client API Service",
    description="A thin wrapper around the mail client implementation (GmailClient).",
    version="1.0.0",
)
```

### Router
Defines URL routing with a common prefix for all mail endpoints.
```python
router = APIRouter(prefix="/messages")
```

### Dependencies

#### get_mail_client() -> Client
Dependency injection function that provides mail client instances to endpoints. Handles authentication errors gracefully.

**Returns:**
- `Client`: Configured mail client instance from `get_client(interactive=False)`

**Raises:**
- `HTTPException`: Status 503 with service initialization error details when `RuntimeError` occurs

**Implementation:**
```python
def get_mail_client() -> Client:
    try:
        client = get_client(interactive=False)
        return client
    except RuntimeError as e:
        logger.error("Failed to initialize mail client: %s", e)
        raise HTTPException(
            status_code=503,
            detail=f"Service initialization failed. Authentication error: {e}",
        ) from e
```

#### MailClientDep
Type alias that simplifies dependency injection syntax in endpoint functions.
```python
MailClientDep = Annotated[Client, Depends(get_mail_client)]
```

### Models

#### MessageSummary
Simple model for message list responses with optional fields.
```python
class MessageSummary(BaseModel):
    id: str
    from_: str | None = None
    subject: str | None = None
    date: str | None = None
```

#### MessageDetail
Complete model for single message responses with all required fields.
```python
class MessageDetail(BaseModel):
    id: str
    from_: str
    to: str
    date: str
    subject: str
    body: str
```

### Endpoints

#### get_messages_summary(client: MailClientDep, max_results: int = 10) -> list[MessageSummary]
**GET /messages** - Returns a list of message summaries. Converts client messages to MessageSummary objects.

**Parameters:**
- `client` (MailClientDep): Injected mail client instance via dependency injection
- `max_results` (int, optional): Maximum number of messages to return. Default: 10

**Returns:**
- `list[MessageSummary]`: List of message summary objects with id, from_, subject, and date fields

**Raises:**
- `HTTPException`: Status 500 with error details when message fetching fails

**Implementation:**
```python
@router.get("", response_model=list[MessageSummary])
def get_messages_summary(client: MailClientDep, max_results: int = 10) -> list[MessageSummary]:
    try:
        return [
            MessageSummary(
                id=msg.id,
                from_=msg.from_,
                subject=msg.subject,
                date=msg.date,
            )
            for msg in client.get_messages(max_results=max_results)
        ]
    except Exception as e:
        logger.error("Error fetching messages: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {e}")
```

#### get_message_detail(message_id: str, client: MailClientDep) -> MessageDetail
**GET /messages/{message_id}** - Returns complete details for a single message. Maps all client message fields to MessageDetail.

**Parameters:**
- `message_id` (str): Unique identifier of the message to retrieve
- `client` (MailClientDep): Injected mail client instance via dependency injection

**Returns:**
- `MessageDetail`: Complete message details including id, from_, to, date, subject, and body

**Raises:**
- `HTTPException`: Status 404 with error details when message not found or inaccessible

**Implementation:**
```python
@router.get("/{message_id}", response_model=MessageDetail)
def get_message_detail(message_id: str, client: MailClientDep) -> MessageDetail:
    try:
        msg = client.get_message(message_id)
        return MessageDetail(
            id=msg.id,
            from_=msg.from_,
            to=msg.to,
            date=msg.date,
            subject=msg.subject,
            body=msg.body,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found or inaccessible: {e}")
```

#### mark_message_as_read(message_id: str, client: MailClientDep) -> JSONResponse
**POST /messages/{message_id}/mark-as-read** - Marks a message as read. Returns success JSON or raises error.

**Parameters:**
- `message_id` (str): Unique identifier of the message to mark as read
- `client` (MailClientDep): Injected mail client instance via dependency injection

**Returns:**
- `JSONResponse`: Success message with status 200 and confirmation content

**Raises:**
- `HTTPException`: Status 500 with error details when mark-as-read operation fails

**Implementation:**
```python
@router.post("/{message_id}/mark-as-read", status_code=200)
def mark_message_as_read(message_id: str, client: MailClientDep) -> JSONResponse:
    if client.mark_as_read(message_id):
        return JSONResponse(status_code=200, content={"message": f"Message {message_id} marked as read."})
    raise HTTPException(status_code=500, detail=f"Failed to mark message {message_id} as read.")
```

#### delete_message(message_id: str, client: MailClientDep) -> JSONResponse
**DELETE /messages/{message_id}** - Deletes a message. Returns success JSON or raises error.

**Parameters:**
- `message_id` (str): Unique identifier of the message to delete
- `client` (MailClientDep): Injected mail client instance via dependency injection

**Returns:**
- `JSONResponse`: Success message with status 200 and confirmation content

**Raises:**
- `HTTPException`: Status 500 with error details when delete operation fails

**Implementation:**
```python
@router.delete("/{message_id}", status_code=200)
def delete_message(message_id: str, client: MailClientDep) -> JSONResponse:
    if client.delete_message(message_id):
        return JSONResponse(status_code=200, content={"message": f"Message {message_id} deleted."})
    raise HTTPException(status_code=500, detail=f"Failed to delete message {message_id}.")
```

### Router Registration
Includes the router in the main application to activate all endpoints.
```python
app.include_router(router)
```

## models.py

### MessageSummary
Enhanced model with field descriptions and JSON alias support. The `alias="from"` allows JSON to use "from" instead of "from_".
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

### MessageDetail
Enhanced model with field descriptions and JSON alias support for complete message data.
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

### MessageListResponse
Response wrapper for paginated message lists (not currently used in main.py endpoints).
```python
class MessageListResponse(BaseModel):
    messages: list[MessageSummary] = Field(..., description="List of message summaries")
    count: int = Field(..., description="Number of messages returned")
```

### SuccessResponse
Generic success response model (not currently used in main.py endpoints).
```python
class SuccessResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")
```

### ErrorResponse
Error response model (not currently used in main.py endpoints).
```python
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")
```

## Package Imports

### main.py imports:
- `import logging`
- `from typing import Annotated`
- `from fastapi import APIRouter, Depends, FastAPI, HTTPException`
- `from fastapi.responses import JSONResponse`
- `from pydantic import BaseModel`
- `from mail_client_api import Client, get_client`

### models.py imports:
- `from pydantic import BaseModel, Field`