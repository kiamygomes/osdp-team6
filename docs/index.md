# Welcome to the Professional Python Template

This professional-grade Python template demonstrates component-based architecture for an AI-powered email assistant. The project showcases modern development practices through a distributed mail client system with clean abstractions and comprehensive tooling.

## System Overview

The mail client system demonstrates distributed architecture patterns through four main components:

- **Mail Client API**: Abstract base classes and interfaces for mail client operations
- **Gmail Client Implementation**: Gmail API implementation of the mail client interface with OAuth2 authentication
- **Mail Client Service**: FastAPI web service exposing mail operations through REST endpoints
- **Mail Client Adapter**: HTTP client adapter implementing the mail client interface for remote service access

Note: The repository includes an auto-generated HTTP client (`mail_client_service_client`). This generated package is stored under `src/mail_client_service_client/` as a nested package directory (`mail_client_api_service_client/`) and may not follow the `src/` layout used by the other components. See the CONTRIBUTING.md for instructions on installing or regenerating the client.

## Key Features

- **Component-Based Architecture**: Clean separation of concerns with well-defined interfaces
- **Distributed System Design**: Local and remote access through identical APIs
- **Professional Toolchain**: Automated quality assurance with Ruff, MyPy, and pytest
- **Comprehensive Testing**: Unit, integration, and end-to-end test coverage with 93%+ coverage
- **Modern Python Practices**: Type hints, dependency injection, and interface-implementation patterns
- **Production-Ready CI/CD**: CircleCI pipeline with automated validation and deployment

## Getting Started

1. **Setup**: Install dependencies with `uv sync --all-packages --extra dev`
2. **Authentication**: Configure Google OAuth credentials
3. **Run Service**: Start the FastAPI service with `uv run uvicorn src.mail_client_service.main:app --reload`
4. **Run Tests**: Execute `uv run pytest src/ tests/ -m "not local_credentials" -v`
5. **View Docs**: Start documentation server with `uv run mkdocs serve`

This documentation site provides detailed information about the project's architecture, API contracts, testing strategies, and usage guidelines.
