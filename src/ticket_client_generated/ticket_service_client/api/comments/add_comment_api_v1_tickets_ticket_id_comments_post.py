from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.comment_create_request import CommentCreateRequest
from ...models.comment_response import CommentResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    ticket_id: UUID,
    *,
    body: CommentCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-user-id"] = x_user_id

    headers["x-project-key"] = x_project_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/tickets/{ticket_id}/comments",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CommentResponse | HTTPValidationError | None:
    if response.status_code == 201:
        response_201 = CommentResponse.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CommentResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    ticket_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CommentCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> Response[CommentResponse | HTTPValidationError]:
    """Add a comment to a ticket

     Add a new comment to an existing ticket.

    Returns 404 if the ticket is not found.

    Args:
        ticket_id (UUID):
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (CommentCreateRequest): Schema for adding a comment to a ticket.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CommentResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        ticket_id=ticket_id,
        body=body,
        x_user_id=x_user_id,
        x_project_key=x_project_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    ticket_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CommentCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> CommentResponse | HTTPValidationError | None:
    """Add a comment to a ticket

     Add a new comment to an existing ticket.

    Returns 404 if the ticket is not found.

    Args:
        ticket_id (UUID):
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (CommentCreateRequest): Schema for adding a comment to a ticket.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CommentResponse | HTTPValidationError
    """

    return sync_detailed(
        ticket_id=ticket_id,
        client=client,
        body=body,
        x_user_id=x_user_id,
        x_project_key=x_project_key,
    ).parsed


async def asyncio_detailed(
    ticket_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CommentCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> Response[CommentResponse | HTTPValidationError]:
    """Add a comment to a ticket

     Add a new comment to an existing ticket.

    Returns 404 if the ticket is not found.

    Args:
        ticket_id (UUID):
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (CommentCreateRequest): Schema for adding a comment to a ticket.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CommentResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        ticket_id=ticket_id,
        body=body,
        x_user_id=x_user_id,
        x_project_key=x_project_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    ticket_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CommentCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> CommentResponse | HTTPValidationError | None:
    """Add a comment to a ticket

     Add a new comment to an existing ticket.

    Returns 404 if the ticket is not found.

    Args:
        ticket_id (UUID):
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (CommentCreateRequest): Schema for adding a comment to a ticket.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CommentResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            ticket_id=ticket_id,
            client=client,
            body=body,
            x_user_id=x_user_id,
            x_project_key=x_project_key,
        )
    ).parsed
