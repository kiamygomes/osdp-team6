# Component Guide

This guide provides detailed information about each component in the system.

## ticket_api

**Purpose**: Foundation layer that defines the contract all implementations must follow.

This package contains the abstract interface and domain models that establish the "what" without specifying the "how". It defines the `TicketServiceAPI` abstract base class with method signatures for all ticket operations, along with immutable dataclasses for `Ticket` and `Comment` objects. The package also includes enumerations for ticket status and priority levels, plus custom exceptions for error handling.

**Key Files**:
- `interface.py` - Abstract base class with all method signatures
- `models.py` - Frozen dataclasses and enumerations
- `exceptions.py` - ServiceError and TicketNotFoundError

**Design Philosophy**: Zero external dependencies, uses only Python standard library. This ensures the interface can be implemented by any backend without forcing specific technology choices.

**Dependencies**: None (stdlib only)  
**Test Coverage**: 100%

---

## ticket_impl

**Purpose**: Concrete implementation that integrates with Jira Cloud.

This component implements the `TicketServiceAPI` interface by communicating with Jira's REST API v3. It handles OAuth 2.0 authentication flows including initial authorization, token storage, and automatic refresh when tokens expire. The implementation abstracts away Jira-specific details like issue keys by using UUIDs, and converts between Jira's data format and the domain models defined in ticket_api.

**Key Files**:
- `impl.py` - Main TicketImpl class implementing the interface
- `jira_client.py` - Low-level HTTP calls to Jira REST API
- `oauth.py` - OAuth 2.0 authorization and token management
- `storage.py` - SQLAlchemy models for persisting tokens and mappings
- `config.py` - Environment-based configuration

**Key Features**: Automatic token refresh before expiration, UUID-to-Jira-key mapping for clean abstractions, conversion to Atlassian Document Format for rich text, comprehensive error handling that maps Jira errors to domain exceptions.

**Dependencies**: ticket_api, httpx, SQLAlchemy, pydantic  
**Test Coverage**: 95%+

---

## ticket_service

**Purpose**: Standalone FastAPI web service exposing ticket operations over HTTP.

This component wraps the ticket_impl implementation and exposes it through RESTful HTTP endpoints. It provides a complete OAuth 2.0 flow for user authentication, cookie-based session management, and automatic OpenAPI documentation generation. The service validates all requests and responses using Pydantic models and provides comprehensive error handling with appropriate HTTP status codes.

**Key Files**:
- `main.py` - FastAPI application with all endpoint definitions
- `models.py` - Pydantic models for request/response validation

**Available Endpoints**:
- Authentication endpoints for OAuth login, callback, logout, and status checking
- CRUD operations for tickets with filtering and pagination
- Comment management for adding and retrieving ticket comments
- Health check endpoint for monitoring
- Interactive Swagger UI documentation

**Deployment**: Can be run locally with uvicorn or deployed to cloud platforms like Vercel, Render, or AWS. Supports CORS configuration for web clients and includes comprehensive logging.

**Dependencies**: ticket_api, ticket_impl, FastAPI, uvicorn  
**Test Coverage**: 90%+

---

## ticket_client_generated

**Purpose**: Type-safe HTTP client automatically generated from OpenAPI specification.

This component is created by running openapi-python-client against the ticket_service's OpenAPI spec. It provides type-safe async methods for every endpoint, with proper request serialization and response deserialization. The generated code includes all the necessary models and handles HTTP communication details.

**Generation Process**: The client is regenerated whenever the service's API changes by running the openapi-python-client tool against the running service's OpenAPI JSON endpoint.

**Usage Note**: While this client can be used directly, it's recommended to use ticket_client_adapter instead, which wraps this generated client with additional reliability features and a cleaner interface that matches the domain API.

**Dependencies**: httpx, attrs, python-dateutil  
**Test Coverage**: Basic smoke tests

---

## ticket_client_adapter

**Purpose**: Production-ready adapter that wraps the generated client with enterprise reliability features.

This component implements the same `TicketServiceAPI` interface as ticket_impl, but communicates with a remote ticket_service over HTTP instead of directly with Jira. It wraps the auto-generated client and adds retry logic with exponential backoff, circuit breaker pattern to prevent cascading failures, idempotency keys for safe retries, and correlation IDs for request tracing.

**Key Files**:
- `client.py` - RemoteTicketService class implementing TicketServiceAPI

**Reliability Features**:
- **Retry Logic**: Automatically retries failed requests with exponential backoff and jitter, respecting Retry-After headers
- **Circuit Breaker**: Opens after consecutive failures to prevent overwhelming a struggling service, automatically recovers after a timeout
- **Idempotency**: Generates deterministic keys for create/update/delete operations to prevent duplicates on retry
- **Observability**: Adds correlation IDs to all requests for distributed tracing, includes structured logging with context

**Why Use This**: Provides the same clean interface as using ticket_impl directly, but with all the reliability features needed for production microservices. Allows swapping between local and remote implementations without changing application code.

**Dependencies**: ticket_api, ticket_client_generated  
**Test Coverage**: 95%+
