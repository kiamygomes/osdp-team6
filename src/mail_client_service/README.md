# Mail Client Service

## Overview
FastAPI web service exposing mail operations through REST endpoints. This package provides a production-ready HTTP API that wraps the mail client functionality, enabling remote access to mail operations with proper error handling, authentication, and documentation.

## Architecture

```
mail_client_service/
├── main.py          # FastAPI application and endpoints
├── models.py        # Pydantic data models
├── constants.py     # HTTP status codes and error messages
└── tests/           # Test suite
```

## Files

### main.py
Contains the FastAPI application with mail-related endpoints that handle HTTP requests and responses with precise exception mapping and proper error handling.

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

#### Custom Exceptions
Domain-specific exception classes for precise HTTP status code mapping.

**`NotFoundError`**  
Raised when a requested resource (message) is not found.

**`AuthError`**  
Raised when authentication or authorization fails.

**`RateLimitError`**  
Raised when API rate limits are exceeded.

#### Dependencies

**`get_mail_client() -> Client`**  
Returns a configured mail client instance for endpoint dependency injection.

- **Returns:** `Client` - Configured mail client instance
- **Raises:** `HTTPException` - Status 503 (Service Unavailable) when mail client initialization fails

**`MailClientDep`**  
Type alias `Annotated[Client, Depends(get_mail_client)]` for cleaner endpoint signatures.

---

### API Endpoints

#### `GET /messages`
Fetches a list of message summaries.

**Parameters:**
- `max_results` (int, optional): Maximum number of messages to return. Default: 10

**Response:** `200 OK`
```json
[
  {
    "id": "msg_123",
    "from": "sender@example.com",
    "to": "recipient@example.com",
    "date": "2024-01-01",
    "subject": "Test Subject"
  }
]
```

**Error Responses:**
- `401 Unauthorized` - Authentication failed
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Unexpected error

---

#### `GET /messages/{message_id}`
Fetches full details of a single message.

**Parameters:**
- `message_id` (str): Unique identifier of the message

**Response:** `200 OK`
```json
{
  "id": "msg_123",
  "from": "sender@example.com",
  "to": "recipient@example.com",
  "date": "2024-01-01",
  "subject": "Test Subject",
  "body": "Full message content..."
}
```

**Error Responses:**
- `404 Not Found` - Message doesn't exist
- `401 Unauthorized` - Authentication failed
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Unexpected error

---

#### `POST /messages/{message_id}/mark-as-read`
Marks a message as read.

**Parameters:**
- `message_id` (str): Unique identifier of the message

**Response:** `204 No Content`  
(Empty response body)

**Error Responses:**
- `404 Not Found` - Message doesn't exist
- `401 Unauthorized` - Authentication failed
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Operation failed

---

#### `DELETE /messages/{message_id}`
Deletes a message.

**Parameters:**
- `message_id` (str): Unique identifier of the message

**Response:** `204 No Content`  
(Empty response body)

**Error Responses:**
- `404 Not Found` - Message doesn't exist
- `401 Unauthorized` - Authentication failed
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Operation failed

---

### models.py
Contains Pydantic models with detailed field descriptions and validation for API documentation.

#### `MessageSummary`
Summary information for a message.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | Yes | Unique message identifier |
| `from` | str | Yes | Sender email address |
| `to` | str | Yes | Recipient email address |
| `date` | str | Yes | Message date |
| `subject` | str | Yes | Message subject |

```python
class MessageSummary(BaseModel):
    id: str = Field(..., description="Unique message identifier")
    from_: str = Field(..., alias="from", description="Sender email address")
    to: str = Field(..., description="Recipient email address")
    date: str = Field(..., description="Message date")
    subject: str = Field(..., description="Message subject")

    class Config:
        populate_by_name = True
```

**Note:** The `from` field is aliased from `from_` to avoid Python keyword conflicts. The API accepts and returns `"from"` in JSON.

---

#### `MessageDetail`
Complete message details including body content.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | Yes | Unique message identifier |
| `from` | str | Yes | Sender email address |
| `to` | str | Yes | Recipient email address |
| `date` | str | Yes | Message date |
| `subject` | str | Yes | Message subject |
| `body` | str | Yes | Message body content |

```python
class MessageDetail(BaseModel):
    id: str = Field(..., description="Unique message identifier")
    from_: str = Field(..., alias="from", description="Sender email address")
    to: str = Field(..., description="Recipient email address")
    date: str = Field(..., description="Message date")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message body content")

    class Config:
        populate_by_name = True
```

---

#### Additional Models

**`MessageListResponse`**  
Response wrapper for message list endpoints.
```python
class MessageListResponse(BaseModel):
    messages: list[MessageSummary]
    count: int
```

**`SuccessResponse`**  
Generic success response model.
```python
class SuccessResponse(BaseModel):
    success: bool
    message: str
```

**`ErrorResponse`**  
Error response model for consistent error formatting.
```python
class ErrorResponse(BaseModel):
    error: str
    detail: str | None
```

---

### constants.py
Centralized constants for HTTP status codes and error messages to improve maintainability and consistency.

#### HTTP Status Codes
```python
HTTP_200_OK = 200
HTTP_204_NO_CONTENT = 204
HTTP_401_UNAUTHORIZED = 401
HTTP_404_NOT_FOUND = 404
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503
```

#### Error Messages
```python
ERROR_SERVICE_INIT_FAILED = "Service initialization failed. Authentication error."
ERROR_FETCH_MESSAGES_FAILED = "Failed to fetch messages."
ERROR_FETCH_MESSAGE_FAILED = "Failed to fetch message."
ERROR_MARK_READ_FAILED = "Failed to mark message as read."
ERROR_DELETE_FAILED = "Failed to delete message."
ERROR_MESSAGE_NOT_FOUND = "Message not found."
ERROR_AUTH_FAILED = "Authentication failed."
ERROR_RATE_LIMIT = "Rate limit exceeded. Please try again later."
```

---

## Error Handling Strategy

The service implements precise exception mapping to HTTP status codes:

| Exception | HTTP Status | Use Case |
|-----------|-------------|----------|
| `NotFoundError` | 404 Not Found | Resource (message) doesn't exist |
| `AuthError` | 401 Unauthorized | Authentication/authorization failure |
| `RateLimitError` | 429 Too Many Requests | API rate limit exceeded |
| Generic `Exception` | 500 Internal Server Error | Unexpected errors |
| `RuntimeError` (init) | 503 Service Unavailable | Service initialization failure |

### Logging
- All errors are logged with full stack traces using `logger.exception()`
- User-facing error messages remain generic to avoid exposing internal details
- Message IDs are included in logs for debugging

### Error Response Format
```json
{
  "detail": "Error message here"
}
```

---

## Response Formats

### Successful Responses

**GET Requests (200 OK)**
- Returns JSON body with requested data
- Content-Type: `application/json`

**Mutations (204 No Content)**
- POST and DELETE operations return 204
- Empty response body
- Indicates successful operation

### Error Responses

All error responses follow this format:
```json
{
  "detail": "Human-readable error message"
}
```

Status codes indicate the type of error (see Error Handling Strategy table above).

---

## Running the Service

### Development
```bash
# Using uv (recommended - from project root)
uv run uvicorn src.mail_client_service.main:app --reload

# Alternative: using pip/uvicorn directly
pip install fastapi uvicorn
uvicorn mail_client_service.main:app --reload
```

### Production
```bash
# Using uv (recommended)
uv run uvicorn src.mail_client_service.main:app --host 0.0.0.0 --port 8000

# Alternative: using uvicorn directly
uvicorn mail_client_service.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run tests
pytest src/mail_client_service/tests/

# With coverage
pytest --cov=mail_client_service src/mail_client_service/tests/
```

---

## API Documentation

Once running, interactive API documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Dependencies

### Required Packages
- `fastapi` - Web framework
- `pydantic` - Data validation
- `mail_client_api` - Mail client interface
- `gmail_client_impl` - Gmail implementation

### Development Dependencies
- `pytest` - Testing framework
- `httpx` - Test client for FastAPI

---

## Design Principles

1. **Separation of Concerns**: Models, constants, and business logic are separated
2. **Explicit Status Codes**: All endpoints declare their success status codes
3. **Comprehensive Error Handling**: Each endpoint handles specific exceptions
4. **Clean Code**: Constants eliminate magic numbers and strings
5. **Proper HTTP Semantics**: 
   - 200 for successful queries with data
   - 204 for successful mutations without response data
   - Appropriate 4xx/5xx codes for errors
6. **Security**: No internal error details exposed to clients
7. **Observability**: Full error logging for debugging