# Mail Client API

## Overview
Abstract base classes and interfaces for mail client operations. This package defines the core contracts that all mail client implementations must follow, ensuring consistent behavior across different implementations.

## Purpose
- Define abstract base classes for mail client operations
- Provide stable interfaces for message handling and client functionality
- Enable dependency injection through factory functions
- Ensure type safety and interface compliance across implementations

## Architecture

### Component Design
The package exposes one abstract base class focused on mailbox operations—fetch, delete, mark-as-read, and iterate. It depends only on the `Message` abstraction.

### API Integration
```python
from mail_client_api import Client, get_client
from mail_client_api.message import Message

client: Client = get_client()
for msg in client.get_messages(max_results=5):
    subject: str = msg.subject
```

### Dependency Injection
Implementation packages (for example `gmail_client_impl`) replace the factory at import time:
```python
import gmail_client_impl  # rebinds mail_client_api.get_client

from mail_client_api import get_client
client = get_client(interactive=False)
```

## API Reference

### Client Abstract Base Class
```python
class Client(ABC):
    ...
```

#### Methods
- `get_message(message_id: str) -> Message`: Return a single message.
- `delete_message(message_id: str) -> bool`: Remove the message from the mailbox.
- `mark_as_read(message_id: str) -> bool`: Clear the unread flag.
- `get_messages(max_results: int = 10) -> Iterator[Message]`: Yield messages lazily.

### Factory Function
`get_client(*, interactive: bool = False) -> Client`: Returns the bound implementation or raises `NotImplementedError` if none registered.

## Usage Examples

### Basic Operations
```python
from mail_client_api import get_client

client = get_client(interactive=False)
for message in client.get_messages(max_results=3):
    print(f"{message.id}: {message.subject}")
```

### Message Management
```python
from mail_client_api import get_client

client = get_client()
important = client.get_message("important_msg_123")
client.mark_as_read(important.id)
```

## Implementation Checklist
1. Implement every method in the abstract base class.
2. Return objects compatible with `mail_client_api.message.Message`.
3. Publish a factory (`get_client_impl`) and assign it to `mail_client_api.get_client`.
4. Honour the `interactive` flag (prompting only when `True`).

## Quick Start

1. **Install an implementation** (e.g., Gmail client):
   ```python
   import gmail_client_impl  # This registers the implementation
   ```

2. **Use the client**:
   ```python
   from mail_client_api import get_client
   
   client = get_client(interactive=False)
   
   # List recent messages
   for message in client.get_messages(max_results=5):
       print(f"{message.from_}: {message.subject}")
   
   # Get full message content
   if messages := list(client.get_messages(max_results=1)):
       full_msg = client.get_message(messages[0].id)
       print(f"Body: {full_msg.body}")
   ```

3. **Alternative: Use the HTTP adapter for remote access**:
   ```python
   from mail_client_adapter import ServiceClientAdapter
   
   # Requires running: uv run uvicorn src.mail_client_service.main:app --reload
   client = ServiceClientAdapter("http://localhost:8000")
   
   # Same interface as above
   for message in client.get_messages(max_results=5):
       print(f"{message.from_}: {message.subject}")
   ```

## Testing
```bash
uv run pytest src/mail_client_api/tests/ -q
uv run pytest src/mail_client_api/tests/ --cov=src/mail_client_api --cov-report=term-missing
```