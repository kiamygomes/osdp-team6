# Ticket API

The `ticket_api` package provides the foundational abstract interface and data models for the OSDP Jira Service ticketing microservice. This package defines the contract that all ticketing service implementations must follow, ensuring consistency and interoperability across different external ticketing systems (Jira, Linear, GitHub Issues, etc.).

## Architecture Overview

The Ticket API serves as the foundation layer in a component-based architecture:

```
┌─────────────────────────────────────────┐
│           Client Applications           │
├─────────────────────────────────────────┤
│        ticket_client_adapter            │
├─────────────────────────────────────────┤
│          ticket_service                 │
├─────────────────────────────────────────┤
│           ticket_impl                   │
├─────────────────────────────────────────┤
│          ticket_api (This Package)      │
└─────────────────────────────────────────┘
```

## Core Components

### Data Models (`models.py`)

#### Ticket Model
The central entity representing a support ticket, issue, or task:

```python
@dataclass(frozen=True)
class Ticket:
    id: UUID                     # Unique identifier
    title: str                   # Brief description (1-200 chars)
    description: str             # Detailed description (1-5000 chars)
    status: TicketStatus        # Current workflow state
    priority: TicketPriority    # Importance level
    assignee: str | None        # Assigned person (optional)
    reporter: str               # Person who created the ticket
    created_at: datetime        # Creation timestamp (UTC)
    updated_at: datetime        # Last modification timestamp (UTC)
    comments: list[Comment]     # Associated comments
```

**Note:** Ticket is an immutable frozen dataclass. State changes should be handled through service methods, not on the model itself.

#### Comment Model
Immutable comments associated with tickets:

```python
@dataclass(frozen=True)
class Comment:
    id: UUID                    # Unique identifier
    ticket_id: UUID            # Parent ticket reference
    author: str                # Comment author
    content: str               # Comment text (1-2000 chars)
    created_at: datetime       # Creation timestamp (UTC)
```

#### Enumerations

**TicketStatus**: Workflow states
- `OPEN`: Newly created, awaiting action
- `IN_PROGRESS`: Currently being worked on
- `RESOLVED`: Issue has been fixed
- `CLOSED`: Ticket is complete and closed

**TicketPriority**: Importance levels
- `LOW`: Minor issues, low impact
- `MEDIUM`: Standard priority (default)
- `HIGH`: Important issues requiring prompt attention
- `CRITICAL`: Urgent issues requiring immediate action

### Abstract Interface (`interface.py`)

#### TicketServiceAPI
Abstract base class defining all ticketing operations that implementations must provide:

```python
class TicketServiceAPI(ABC):
    @abstractmethod
    async def create_ticket(
        self,
        title: str,
        description: str,
        reporter: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assignee: str | None = None
    ) -> Ticket:
        """Create a new ticket in the system."""
    
    @abstractmethod
    async def get_ticket(self, ticket_id: UUID) -> Ticket | None:
        """Retrieve a ticket by its ID."""
    
    @abstractmethod
    async def list_tickets(
        self,
        status: TicketStatus | None = None,
        assignee: str | None = None,
        reporter: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Ticket]:
        """List tickets with optional filtering and pagination."""
    
    @abstractmethod
    async def update_ticket(
        self,
        ticket_id: UUID,
        title: str | None = None,
        description: str | None = None,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        assignee: str | None = None
    ) -> Ticket | None:
        """Update an existing ticket."""
    
    @abstractmethod
    async def delete_ticket(self, ticket_id: UUID) -> bool:
        """Delete a ticket from the system."""
    
    @abstractmethod
    async def add_comment(
        self,
        ticket_id: UUID,
        author: str,
        content: str
    ) -> Comment | None:
        """Add a comment to an existing ticket."""
    
    @abstractmethod
    async def get_ticket_comments(self, ticket_id: UUID) -> list[Comment]:
        """Retrieve all comments for a specific ticket."""
```

## Key Features

### Type Safety
- **Full Type Hints**: All methods, models, and fields include comprehensive type annotations
- **MyPy Compatibility**: Passes strict mypy type checking
- **IDE Support**: Excellent autocomplete and error detection in modern IDEs

### Data Validation
- **Pydantic Models**: Comprehensive field validation with clear error messages
- **Length Constraints**: Appropriate limits for all text fields
- **Required Fields**: Clear distinction between required and optional fields
- **Format Validation**: Email format validation, UUID validation, etc.

### Immutability and Consistency
- **Immutable Comments**: Comments cannot be modified once created (audit trail)
- **Timestamp Management**: Automatic UTC timestamp handling
- **State Consistency**: Business logic methods ensure consistent state updates

### Extensibility
- **Easy Extension**: Add new fields or methods without breaking existing code
- **Backward Compatibility**: Designed for evolution without breaking changes
- **Plugin Architecture**: Support for custom implementations and extensions

## Usage Examples

### Basic Ticket Operations

```python
from ticket_api import Ticket, TicketStatus, TicketPriority, TicketServiceAPI

# Models are immutable data classes - state changes go through the service
service: TicketServiceAPI  # Implementation injected at runtime

# Create a new ticket
ticket = await service.create_ticket(
    title="Login system not responding",
    description="Users report that the login page is not loading properly.",
    reporter="support@company.com",
    priority=TicketPriority.HIGH
)

# Add a comment through the service
comment = await service.add_comment(
    ticket_id=ticket.id,
    author="dev@company.com",
    content="Investigating the issue. Checking server logs for errors."
)

# Update ticket status through the service
updated_ticket = await service.update_ticket(
    ticket_id=ticket.id,
    status=TicketStatus.IN_PROGRESS,
    assignee="senior-dev@company.com"
)

print(f"Ticket {updated_ticket.id} is now assigned to {updated_ticket.assignee}")
print(f"Status: {updated_ticket.status.value}")
print(f"Comments: {len(updated_ticket.comments)}")
```

### Implementing the Service Interface

```python
from ticket_api import TicketServiceAPI, Ticket, Comment
from uuid import UUID

class JiraTicketService(TicketServiceAPI):
    def __init__(self, jira_client):
        self.jira_client = jira_client
    
    async def create_ticket(self, title: str, description: str, reporter: str,
                          priority: TicketPriority = TicketPriority.MEDIUM,
                          assignee: str | None = None) -> Ticket:
        # Create ticket in Jira
        jira_issue = await self.jira_client.create_issue({
            "fields": {
                "summary": title,
                "description": description,
                "priority": {"name": priority.value.title()},
                "reporter": {"emailAddress": reporter},
                "assignee": {"emailAddress": assignee} if assignee else None
            }
        })
        
        # Convert Jira response to our Ticket model
        return Ticket(
            id=UUID(jira_issue["id"]),
            title=jira_issue["fields"]["summary"],
            description=jira_issue["fields"]["description"],
            reporter=reporter,
            priority=priority,
            assignee=assignee
        )
    
    async def get_ticket(self, ticket_id: UUID) -> Ticket | None:
        try:
            jira_issue = await self.jira_client.get_issue(str(ticket_id))
            return self._convert_jira_issue_to_ticket(jira_issue)
        except JiraNotFoundError:
            return None
    
    # ... implement other abstract methods
```

### Data Model Examples

```python
from ticket_api import Ticket, Comment
from uuid import uuid4
from datetime import datetime, UTC

# Create a valid ticket
ticket = Ticket(
    title="Valid ticket title",
    description="This is a valid description with appropriate length.",
    reporter="user@example.com"
)

# Create a comment
comment = Comment(
    ticket_id=ticket.id,
    author="dev@example.com",
    content="This is a comment"
)

# Models are frozen (immutable) - attempts to modify will raise FrozenInstanceError
try:
    ticket.title = "New title"  # This will raise FrozenInstanceError
except Exception as e:
    print(f"Cannot modify frozen dataclass: {type(e).__name__}")
```

**Note:** Data validation happens at the API layer (in `ticket_service`) via Pydantic models, not on the domain models themselves. This separates concerns: the API validates input, domain models just hold data.

## Testing

The package includes comprehensive tests ensuring contract compliance and data model validation:

### Test Structure

**test_api_contract.py** - Core contract validation
- Ticket and Comment dataclass creation
- Comment model immutability testing
- Enum value validation
- Abstract interface enforcement
- Dataclass field requirements

**test_edge_cases.py** - Boundary and edge case testing
- Unicode content handling
- Maximum field length validation
- Empty and null value handling
- Timestamp consistency
- Immutable frozen dataclass behavior

### Test Categories

- **Model Creation**: Dataclass instantiation and field defaults
- **Immutability**: Frozen dataclass behavior and FrozenInstanceError
- **Interface Contract**: Abstract method enforcement
- **Enum Validation**: Status and Priority enum values
- **Edge Cases**: Unicode, boundary conditions, and error scenarios

### Running Tests

```bash
# All ticket API tests
uv run pytest src/ticket_api/tests/ -v

# Specific test files
uv run pytest src/ticket_api/tests/test_api_contract.py -v
uv run pytest src/ticket_api/tests/test_edge_cases.py -v

# Coverage reporting
uv run pytest src/ticket_api/tests/ --cov=ticket_api --cov-report=term-missing
```

### Test Coverage

- **Coverage**: 100% line and branch coverage
- **Test Count**: 16 comprehensive test cases
- **Model Testing**: Dataclass creation, defaults, and field handling
- **Error Handling**: Immutability violations and type errors

## Integration with External Systems

### Jira Integration
The abstract interface maps naturally to Jira's REST API:

| Ticket API Method | Jira REST API Endpoint |
|------------------|------------------------|
| `create_ticket()` | `POST /rest/api/3/issue` |
| `get_ticket()` | `GET /rest/api/3/issue/{issueIdOrKey}` |
| `list_tickets()` | `GET /rest/api/3/search` |
| `update_ticket()` | `PUT /rest/api/3/issue/{issueIdOrKey}` |
| `delete_ticket()` | `DELETE /rest/api/3/issue/{issueIdOrKey}` |
| `add_comment()` | `POST /rest/api/3/issue/{issueIdOrKey}/comment` |

### Other Ticketing Systems
The interface is designed to work with various ticketing systems:
- **Linear**: Issues and comments
- **GitHub Issues**: Issues and comments
- **Azure DevOps**: Work items and discussions
- **ServiceNow**: Incidents and work notes

## Development Guidelines

### Adding New Fields
When extending the models, follow these guidelines:

1. **Add to Model**: Add the field to the appropriate frozen dataclass
2. **Update Interface**: Add parameters to relevant abstract methods if needed
3. **Maintain Compatibility**: Use optional fields with defaults for backward compatibility
4. **Add Tests**: Include comprehensive tests for new functionality
5. **Update Documentation**: Update docstrings and README
6. **Keep Models Simple**: Business logic belongs in services, not models

### Error Handling
The interface defines expected exceptions:
- `ValueError`: Invalid input parameters
- `ServiceError`: External service communication errors (implementation-specific)

### Performance Considerations
- **Async Methods**: All interface methods are async for non-blocking operations
- **Pagination**: `list_tickets()` includes limit/offset for large result sets
- **Lazy Loading**: Comments are included in tickets but can be fetched separately

## Dependencies

### Runtime Dependencies
- **None**: Uses only Python standard library (dataclasses, ABC, enums, etc.)

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **mypy**: Static type checking
- **ruff**: Linting and formatting

## Version Compatibility

- **Python**: 3.11+
- **Type Hints**: Uses modern Python type hint syntax (`str | None` instead of `Optional[str]`)
- **Dataclasses**: Uses Python 3.10+ frozen dataclasses for immutable models

## Contributing

When contributing to the ticket API:

1. **Maintain Interface Stability**: Changes to the abstract interface should be backward compatible
2. **Add Comprehensive Tests**: All new functionality must include tests
3. **Update Documentation**: Keep README and docstrings current
4. **Follow Type Hints**: All code must include proper type annotations
5. **Validate with Tools**: Ensure code passes mypy, ruff, and pytest

## License

This package is part of the OSDP Jira Service project and follows the same licensing terms.