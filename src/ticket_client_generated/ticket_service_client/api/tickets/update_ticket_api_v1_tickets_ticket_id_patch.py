from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.ticket_response import TicketResponse
from ...models.ticket_update_request import TicketUpdateRequest
from ...types import Response


def _get_kwargs(
    ticket_id: UUID,
    *,
    body: TicketUpdateRequest,
    x_user_id: str,
    x_project_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-user-id"] = x_user_id

    headers["x-project-key"] = x_project_key

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/api/v1/tickets/{ticket_id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TicketResponse | None:
    if response.status_code == 200:
        response_200 = TicketResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | TicketResponse]:
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
    body: TicketUpdateRequest,
    x_user_id: str,
    x_project_key: str,
) -> Response[HTTPValidationError | TicketResponse]:
    """Update a ticket

     Update an existing ticket. All fields are optional - only provided fields will be updated.

    Returns 404 if the ticket is not found.

    Args:
        ticket_id (UUID):
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (TicketUpdateRequest): Schema for updating an existing ticket. All fields are
            optional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketResponse]
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
    body: TicketUpdateRequest,
    x_user_id: str,
    x_project_key: str,
) -> HTTPValidationError | TicketResponse | None:
    """Update a ticket

     Update an existing ticket. All fields are optional - only provided fields will be updated.

    Returns 404 if the ticket is not found.

    Args:
        ticket_id (UUID):
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (TicketUpdateRequest): Schema for updating an existing ticket. All fields are
            optional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketResponse
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
    body: TicketUpdateRequest,
    x_user_id: str,
    x_project_key: str,
) -> Response[HTTPValidationError | TicketResponse]:
    """Update a ticket

     Update an existing ticket. All fields are optional - only provided fields will be updated.

    Returns 404 if the ticket is not found.

    Args:
        ticket_id (UUID):
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (TicketUpdateRequest): Schema for updating an existing ticket. All fields are
            optional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketResponse]
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
    body: TicketUpdateRequest,
    x_user_id: str,
    x_project_key: str,
) -> HTTPValidationError | TicketResponse | None:
    """Update a ticket

     Update an existing ticket. All fields are optional - only provided fields will be updated.

    Returns 404 if the ticket is not found.

    Args:
        ticket_id (UUID):
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (TicketUpdateRequest): Schema for updating an existing ticket. All fields are
            optional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketResponse
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
