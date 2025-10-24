# Contributing to Mail Client Service

## Architecture Overview
### Components

The repository consists of several Python packages organized in a modular architecture:

- `src/mail_client_api/` — Abstract base classes and interfaces for mail client operations
- `src/gmail_client_impl/` — Gmail API implementation of the mail client interface with OAuth2 authentication
- `src/mail_client_adapter/` — HTTP client adapter implementing the mail client interface for remote service access
- `src/mail_client_service/` — FastAPI web service exposing mail operations through REST endpoints
- `src/mail_client_service_client/` — Auto-generated HTTP client for service communication
- `main.py` — Demo entrypoint for local testing and authentication
- `tests/` — Integration & end-to-end tests (pytest + markers)
- `docs/` — MkDocs documentation sources

At runtime, code depends on the interface (`mail_client_api.Client`), not the implementation. The Gmail implementation is swappable (e.g., with a mock or a future provider).

### Interface Design

Interfaces are expressed with Abstract Base Classes (ABCs) and type hints to make the contract explicit and stable.
```python
# src/mail_client_api/client.py
from abc import ABC, abstractmethod
from typing import Any

class Client(ABC):
    @abstractmethod
    def get_messages(self, max_results: int = 10) -> list[dict[str, Any]]:
        """Return a list of message summaries."""
```

Why this design?
- Clear separation of what (contract) from how (provider).
- Easy to mock in tests.
- Consumers remain stable even if implementation details change.

Extra credit – ABC vs `typing.Protocol`
- ABC enforces implementation at runtime (subclass must implement abstract methods).
- Protocol enables static structural typing (duck typing) and has no runtime enforcement.
- This repo favors ABCs to catch contract violations during execution while still benefiting from type hints.
  
### Implementation Details

The Gmail package implements the `Client` interface, delegating calls to the Google/Gmail APIs. The rest of the code should import only the abstract `Client` to avoid coupling to Gmail specifics.
```python
# src/gmail_client_impl/gmail_client.py
from mail_client_api import Client

class GmailClient(Client):
    ...
    def get_messages(self, max_results: int = 10) -> list[dict]:
        # calls Gmail API, normalizes fields, returns list[dict]
        ...
```
### Dependency Injection

This project uses constructor/function-level injection at the composition root. Create the concrete client and pass it where a `Client` is required.
```python
# main.py (composition root)
from mail_client_api import Client
from gmail_client_impl import GmailClient

def run_demo() -> None:
    client: Client = GmailClient(...)  # e.g., credentials from env/files
    messages = client.get_messages(max_results=10)
    for m in messages:
        print(m)

if __name__ == "__main__":
    run_demo()
```

What this enables:
- Swap implementations (e.g., a fake client in tests).
- Test higher-level code without touching Gmail.
- Keep consumers stable as implementations evolve.

## Repository Structure
### Project Organization
```
.
├── src/
│   ├── mail_client_api/           # Abstract base classes and interfaces for mail client operations
│   ├── gmail_client_impl/         # Gmail API implementation with OAuth2 authentication
│   ├── mail_client_adapter/       # HTTP client adapter for remote service access
│   ├── mail_client_service/       # FastAPI web service exposing REST endpoints
│   └── mail_client_service_client/# Auto-generated HTTP client for service communication
├── tests/
│   ├── integration/              # Component interaction tests
│   └── e2e/                     # Full application workflow tests
├── docs/                        # MkDocs documentation sources
│   ├── api/                     # API reference documentation
│   └── *.md                     # General documentation
├── .circleci/                   # CircleCI pipeline configuration
├── main.py                      # Local demo / auth bootstrap
├── pyproject.toml              # Root workspace configuration
├── requirements.txt            # Top-level dependencies
├── mkdocs.yml                  # Documentation site configuration
└── credentials.json            # Gmail API credentials (gitignored)
```
### Configuration Files

#### Root Configuration
- `pyproject.toml`: Declares workspace configuration, shared dependencies, and tool configs (Ruff, Pytest, MyPy)
- `requirements.txt`: Lists top-level project dependencies
- `mkdocs.yml`: Documentation site configuration

#### Package Configuration
Each package under `src/` has its own configuration:
- Individual `pyproject.toml` files for package-specific metadata and dependencies
- Package-specific README files describing usage and functionality
- Type stub files (`py.typed`) for static typing support

The modular structure allows packages to be used independently or as part of the complete system.

### Package Structure

Each importable package (e.g., `src/mail_client_api/`, `src/gmail_client_impl/`) includes an `__init__.py` that exports the public surface and avoids side effects.
```python
# src/mail_client_api/__init__.py
from .client import Client
__all__ = ["Client"]
```

Keep `__init__.py` slim: export names only; no heavy logic or long import chains.

### Import Guidelines
-Preferred: absolute imports across packages
```python
from mail_client_api import Client
from gmail_client_impl import GmailClient
```
- Relative imports: allowed within the same package for local module organization.
- Avoid circular imports by depending on interfaces from `mail_client_api`, not on concrete classes.

## Testing Strategy
### Testing Philosophy
Follow the “Building Quality In / Effective Unit Testing” principles:
- Fast, Isolated, Repeatable, Self-verifying, Timely tests.
- Use Arrange → Act → Assert; test via the public API; test state/behavior, not method internals.
- Don’t change existing tests when refactoring; add tests for new features/bug fixes.
- 
### Test Organization
```
tests/
├── integration/        # interactions between components
└── e2e/                # end-to-end flows (credentials/env may be required)
```
Markers (examples):
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.circleci
@pytest.mark.local_credentials
```
`__init__.py` in tests:
By convention, omit `__init__.py` in test directories so pytest treats them as test modules (not importable packages). This avoids path/package surprises and keeps tests decoupled from runtime import resolution.

### Test Abstraction Levels
- Unit (when present in packages) — smallest, fastest; mock external systems.
- Integration — verify interface ↔ implementation behavior.
- E2E — validate real flows; keep focused since they’re slower/flakier.

### Code Coverage
- Tool: `pytest-cov`.
- Threshold: 85% target for the base repo (badge reflects ≥85%). If you want hard enforcement locally:
```bash
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=85
```
HTML report:
```bash
uv run pytest --cov=src --cov-report=html
# open htmlcov/index.html
```

## Development Setup

### Prerequisites
- Python 3.11 or higher
- Gmail API credentials (for Gmail implementation)

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/kiamygomes/osdp-team6.git
cd osdp-team6
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Gmail credentials (for Gmail implementation):
- Place `credentials.json` in the root directory
- Run main.py to complete OAuth flow
```bash
python main.py
```

### Development Workflow

#### Running Components
```bash
# Start the FastAPI service
cd src/mail_client_service
uvicorn main:app --reload

# Run the demo client
python main.py

# Generate API client (if service interface changes)
cd src/mail_client_service_client
datamodel-codegen ...
```

#### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m integration             # Only integration tests
pytest -m e2e                     # Only end-to-end tests
pytest -m 'not local_credentials' # Skip tests requiring credentials

# Run tests with coverage
pytest --cov=src --cov-report=html
```

Root vs. component config
- The root `pyproject.toml` owns the workspace definition, dependency graph, and tool settings.
- Packages under `src/` are regular Python packages. If you later add component `pyproject.toml` files, those will own component-specific metadata and dependencies.

### Static Analysis and Code Formatting
- Ruff — linting + formatting
- MyPy — static type checking
```bash
uv run ruff check .
uv run ruff check . --fix
uv run ruff format --check .
uv run ruff format .
uv run mypy src tests
```

Why this matters: consistent style, early error detection, and easier reviews across contributors. All tools run through `uv` to ensure a consistent environment.

### Documentation Generation

MkDocs powers the docs site.
```bash
uv run mkdocs serve   # live-reloading local server
uv run mkdocs build   # outputs static site to ./site
```
### Continuous Integration (CI)

CircleCI pipeline includes:
- Lint/Format/Types — Ruff + MyPy.
- Tests — marker-driven selection for CI stability (e.g., `circleci` set, skip `local_credentials`).
- Artifacts/Reports — coverage & test results uploaded as artifacts.
- Projects may run broader integration tests on protected branches (e.g., main/root) when credentials are available.

