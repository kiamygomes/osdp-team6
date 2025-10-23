# Welcome to the Mail Client Template

This project is a professional-grade template for a modern Python application, built using a component-based architecture with a clear separation between interface and implementation.

## System Overview

The mail client system demonstrates distributed architecture patterns through four main components:

- **Mail Client API**: Abstract base classes defining the contract for mail operations
- **Gmail Client Implementation**: Concrete implementation using Google's Gmail API
- **Mail Client Service**: FastAPI web service exposing mail operations via HTTP REST endpoints
- **Mail Client Adapter**: HTTP client that implements the Client interface for remote service access

## Key Features

- **Interface-Implementation Separation**: Clean abstractions with swappable implementations
- **Dependency Injection**: Runtime binding of implementations to interfaces
- **Distributed Architecture**: Local and remote access through identical interfaces
- **Comprehensive Testing**: Unit, integration, and end-to-end test coverage
- **Modern Toolchain**: Automated code quality with Ruff, MyPy, and pytest
- **Professional CI/CD**: CircleCI pipeline with comprehensive validation

## Getting Started

1. **Setup**: Install dependencies with `uv sync --all-packages --extra dev`
2. **Authentication**: Configure Google OAuth credentials
3. **Run Service**: Start the FastAPI service with `uv run uvicorn src.mail_client_service.main:app --reload`
4. **Run Tests**: Execute `uv run pytest src/ tests/ -m "not local_credentials" -v`
5. **View Docs**: Start documentation server with `uv run mkdocs serve`

This documentation site provides detailed information about the project's architecture, API contracts, testing strategies, and usage guidelines.
