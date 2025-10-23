# Mail Client Adapter

The Mail Client Adapter provides an HTTP-based implementation of the `Client` interface, enabling remote access to mail functionality through REST API calls.

## Overview

The adapter consists of two main classes that work together to provide transparent remote access to mail services:

- **`ServiceClientAdapter`**: Implements the `Client` interface using HTTP calls
- **`ServiceMessage`**: Wraps service responses to provide the `Message` interface

## ServiceClientAdapter

The main adapter class that implements the `Client` interface by delegating method calls to a remote mail service.

### Constructor

```python
ServiceClientAdapter(base_url: str)
```

**Parameters:**
- `base_url` (str): Base URL of the running Mail Client Service (e.g., `"http://localhost:8000"`)

### Methods

#### get_messages(max_results: int = 10) -> Iterator[Message]

Fetches a list of message summaries from the remote service.

**Parameters:**
- `max_results` (int, optional): Maximum number of messages to return. Default: 10

**Returns:**
- Iterator of `ServiceMessage` objects containing message summaries

**Example:**
```python
client = ServiceClientAdapter("http://localhost:8000")
for msg in client.get_messages(max_results=5):
    print(f"{msg.from_}: {msg.subject}")
```

#### get_message(message_id: str) -> Message

Retrieves full details of a single message.

**Parameters:**
- `message_id` (str): Unique identifier of the message

**Returns:**
- `ServiceMessage` object with full message details

**Example:**
```python
message = client.get_message("abc123")
print(f"Subject: {message.subject}")
print(f"Body: {message.body}")
```

#### delete_message(message_id: str) -> bool

Deletes a message by ID.

**Parameters:**
- `message_id` (str): Unique identifier of the message

**Returns:**
- `True` if deletion succeeds, `False` otherwise

**Example:**
```python
success = client.delete_message("abc123")
if success:
    print("Message deleted successfully")
```

#### mark_as_read(message_id: str) -> bool

Marks a message as read.

**Parameters:**
- `message_id` (str): Unique identifier of the message

**Returns:**
- `True` if operation succeeds, `False` otherwise

**Example:**
```python
success = client.mark_as_read("abc123")
if success:
    print("Message marked as read")
```

## ServiceMessage

A wrapper class that implements the `Message` interface for service responses.

### Constructor

```python
ServiceMessage(detail: MessageDetail | MessageSummary)
```

**Parameters:**
- `detail`: Either a `MessageDetail` or `MessageSummary` object from the service

### Properties

All properties return empty strings if the underlying data is not available:

- **`id`** (str): Unique message identifier
- **`from_`** (str): Sender's email address
- **`to`** (str): Recipient's email address (only available in MessageDetail)
- **`date`** (str): Message timestamp
- **`subject`** (str): Message subject line
- **`body`** (str): Full message body content (only available in MessageDetail)

## Usage Example

First, start the mail client service:
```bash
uv run uvicorn src.mail_client_service.main:app --reload
```

Then use the adapter to connect to the running service:
```python
from mail_client_adapter import ServiceClientAdapter

# Create adapter pointing to running service
client = ServiceClientAdapter("http://localhost:8000")

# List messages
messages = list(client.get_messages(max_results=10))
print(f"Found {len(messages)} messages")

# Get full message details
if messages:
    full_message = client.get_message(messages[0].id)
    print(f"Subject: {full_message.subject}")
    print(f"From: {full_message.from_}")
    print(f"Body: {full_message.body}")
    
    # Mark as read
    if client.mark_as_read(messages[0].id):
        print("Message marked as read")
    
    # Delete message
    if client.delete_message(messages[0].id):
        print("Message deleted")
```

## Error Handling

The adapter uses a defensive approach to error handling:

- **Network/HTTP errors**: `delete_message()` and `mark_as_read()` return `False` on any exception
- **Service errors**: `get_messages()` and `get_message()` let exceptions propagate to the caller
- **Missing data**: `ServiceMessage` properties return empty strings for missing fields

## Architecture Benefits

1. **Interface Compliance**: Implements the same `Client` interface as local implementations
2. **Transparent Remote Access**: Client code requires no changes to use remote services
3. **Distributed Architecture**: Enables separation of client and service components
4. **Error Resilience**: Graceful handling of network and service failures
5. **Type Safety**: Maintains strong typing through the `Message` interface