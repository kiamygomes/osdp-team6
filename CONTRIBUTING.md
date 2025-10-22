# CONTRIBUTING.md
## Architecture Overview
### Components

The repository is a `uv` workspace with these primary parts:
- `src/mail_client_api/` — abstract contract for a mail client (the interface).
- `src/gmail_client_impl/` — concrete Gmail implementation of that contract.
- `main.py` — small demo entrypoint (handy for local auth / smoke runs).
- `tests/` — integration & end-to-end tests (pytest + markers).
- `docs/` — MkDocs docs sources.

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
│   ├── mail_client_api/        # Abstract Client (ABC) and public types
│   └── gmail_client_impl/      # GmailClient concrete implementation
├── tests/
│   ├── integration/            # interface <-> implementation tests
│   └── e2e/                    # full-flow tests (may require credentials)
├── docs/                       # MkDocs sources
├── .circleci/                  # CircleCI pipeline config
├── main.py                     # local demo / auth bootstrap
├── pyproject.toml              # workspace + tools configuration
├── mkdocs.yml                  # docs site configuration
└── uv.lock                     # locked dependency set
```
### Configuration Files
- Root `pyproject.toml`
- Declares the `uv` workspace, shared dependencies, and tool configs (Ruff, Pytest, MyPy, etc.).
- Component-level `pyproject.toml`
- Not used in this template. Components are Python packages under `src/`. If you later split packages into independent build units, give each one its own `pyproject.toml` (PEP 621 metadata + local deps).

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

## Development Tools
### Workspace Management

Install & sync
```bash
uv sync --all-packages --extra dev
```
Common tasks
```bash
# run the demo (also performs first-time OAuth)
uv run python main.py

# tests (pick the scope you need)
uv run pytest                            # all tests
uv run pytest src/                       # fast/unit-like tests under src (if present)
uv run pytest -m integration             # only integration
uv run pytest -m e2e                     # only end-to-end
uv run pytest -m 'not local_credentials' # skip tests that need local files
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

