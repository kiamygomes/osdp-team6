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
class Ticket(BaseModel):
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

**Business Logic Methods:**
- `add_comment(author, content)`: Add a new comment and update timestamp
- `update_status(new_status)`: Change ticket status and update timestamp
- `assign_to(assignee)`: Assign ticket to a person and update timestamp

#### Comment Model
Immutable comments associated with tickets:

```python
class Comment(BaseModel):
    id: UUID                    # Unique identifier
    ticket_id: UUID            # Parent ticket reference
    author: str                # Comment author
    content: str               # Comment text (1-2000 chars)
    created_at: datetime       # Creation timestamp (UTC)
    
    model_config = ConfigDict(frozen=True)  # Immutable
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
from ticket_api import Ticket, TicketStatus, TicketPriority

# Create a new ticket
ticket = Ticket(
    title="Login system not responding",
    description="Users report that the login page is not loading properly. Error occurs on both Chrome and Firefox.",
    reporter="support@company.com",
    priority=TicketPriority.HIGH
)

# Add a comment
ticket_with_comment = ticket.add_comment(
    author="dev@company.com",
    content="Investigating the issue. Checking server logs for errors."
)

# Update ticket status
in_progress_ticket = ticket_with_comment.update_status(TicketStatus.IN_PROGRESS)

# Assign the ticket
assigned_ticket = in_progress_ticket.assign_to("senior-dev@company.com")

print(f"Ticket {assigned_ticket.id} is now assigned to {assigned_ticket.assignee}")
print(f"Status: {assigned_ticket.status.value}")
print(f"Comments: {len(assigned_ticket.comments)}")
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

### Data Validation Examples

```python
from ticket_api import Ticket, Comment
from pydantic import ValidationError

# Validation success
valid_ticket = Ticket(
    title="Valid ticket title",
    description="This is a valid description with appropriate length.",
    reporter="user@example.com"
)

# Validation failures
try:
    # Empty title
    invalid_ticket = Ticket(
        title="",
        description="Valid description",
        reporter="user@example.com"
    )
except ValidationError as e:
    print(f"Validation error: {e}")

try:
    # Title too long
    long_title = "x" * 201  # Exceeds 200 character limit
    invalid_ticket = Ticket(
        title=long_title,
        description="Valid description",
        reporter="user@example.com"
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Testing

The package includes comprehensive tests ensuring contract compliance and data model validation:

### Test Structure

**test_api_contract.py** - Core contract validation
- Ticket model creation and validation
- Comment model immutability testing
- Enum value validation
- Abstract interface enforcement
- Business logic method testing

**test_edge_cases.py** - Boundary and edge case testing
- Unicode content handling
- Maximum field length validation
- Empty and null value handling
- Timestamp consistency
- Multiple comment scenarios

### Test Categories

- **Model Validation**: Pydantic field constraints and type checking
- **Business Logic**: Ticket state transitions and comment addition
- **Immutability**: Comment freeze behavior and audit trail
- **Interface Contract**: Abstract method enforcement
- **Edge Cases**: Boundary conditions and error scenarios

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
- **Test Count**: 24 comprehensive test cases
- **Validation**: All Pydantic constraints and business rules
- **Error Handling**: Invalid data and constraint violations

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

1. **Add to Model**: Add the field to the appropriate Pydantic model
2. **Update Interface**: Add parameters to relevant abstract methods if needed
3. **Maintain Compatibility**: Use optional fields with defaults for backward compatibility
4. **Add Tests**: Include comprehensive tests for new functionality
5. **Update Documentation**: Update docstrings and README

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
- **pydantic**: Data validation and serialization

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **mypy**: Static type checking
- **ruff**: Linting and formatting

## Version Compatibility

- **Python**: 3.11+
- **Pydantic**: 2.0+
- **Type Hints**: Uses modern Python type hint syntax (`str | None` instead of `Optional[str]`)

## Contributing

When contributing to the ticket API:

1. **Maintain Interface Stability**: Changes to the abstract interface should be backward compatible
2. **Add Comprehensive Tests**: All new functionality must include tests
3. **Update Documentation**: Keep README and docstrings current
4. **Follow Type Hints**: All code must include proper type annotations
5. **Validate with Tools**: Ensure code passes mypy, ruff, and pytest

## License

This package is part of the OSDP Jira Service project and follows the same licensing terms.