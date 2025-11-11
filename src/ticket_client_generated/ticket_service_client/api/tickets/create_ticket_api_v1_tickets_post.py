from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.ticket_create_request import TicketCreateRequest
from ...models.ticket_response import TicketResponse
from ...types import Response


def _get_kwargs(
    *,
    body: TicketCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-user-id"] = x_user_id

    headers["x-project-key"] = x_project_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/tickets",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TicketResponse | None:
    if response.status_code == 201:
        response_201 = TicketResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TicketResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TicketCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> Response[HTTPValidationError | TicketResponse]:
    """Create a new ticket

     Create a new ticket in Jira.

    Requires X-User-ID and X-Project-Key headers.

    Args:
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (TicketCreateRequest): Schema for creating a new ticket.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_user_id=x_user_id,
        x_project_key=x_project_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: TicketCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> HTTPValidationError | TicketResponse | None:
    """Create a new ticket

     Create a new ticket in Jira.

    Requires X-User-ID and X-Project-Key headers.

    Args:
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (TicketCreateRequest): Schema for creating a new ticket.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_user_id=x_user_id,
        x_project_key=x_project_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TicketCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> Response[HTTPValidationError | TicketResponse]:
    """Create a new ticket

     Create a new ticket in Jira.

    Requires X-User-ID and X-Project-Key headers.

    Args:
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (TicketCreateRequest): Schema for creating a new ticket.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_user_id=x_user_id,
        x_project_key=x_project_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TicketCreateRequest,
    x_user_id: str,
    x_project_key: str,
) -> HTTPValidationError | TicketResponse | None:
    """Create a new ticket

     Create a new ticket in Jira.

    Requires X-User-ID and X-Project-Key headers.

    Args:
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key
        body (TicketCreateRequest): Schema for creating a new ticket.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_user_id=x_user_id,
            x_project_key=x_project_key,
        )
    ).parsed
