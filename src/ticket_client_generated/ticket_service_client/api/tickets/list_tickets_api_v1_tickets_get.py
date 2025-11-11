from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.ticket_list_response import TicketListResponse
from ...models.ticket_status import TicketStatus
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    status: None | TicketStatus | Unset = UNSET,
    assignee: None | str | Unset = UNSET,
    reporter: None | str | Unset = UNSET,
    x_user_id: str,
    x_project_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-user-id"] = x_user_id

    headers["x-project-key"] = x_project_key

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["offset"] = offset

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, TicketStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    json_assignee: None | str | Unset
    if isinstance(assignee, Unset):
        json_assignee = UNSET
    else:
        json_assignee = assignee
    params["assignee"] = json_assignee

    json_reporter: None | str | Unset
    if isinstance(reporter, Unset):
        json_reporter = UNSET
    else:
        json_reporter = reporter
    params["reporter"] = json_reporter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/tickets",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TicketListResponse | None:
    if response.status_code == 200:
        response_200 = TicketListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TicketListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    status: None | TicketStatus | Unset = UNSET,
    assignee: None | str | Unset = UNSET,
    reporter: None | str | Unset = UNSET,
    x_user_id: str,
    x_project_key: str,
) -> Response[HTTPValidationError | TicketListResponse]:
    """List tickets with filtering

     List tickets with optional filtering and pagination.

    All filter parameters are optional. Results are paginated using limit/offset.

    Args:
        limit (int | Unset): Maximum number of tickets to return Default: 100.
        offset (int | Unset): Number of tickets to skip Default: 0.
        status (None | TicketStatus | Unset): Filter by ticket status
        assignee (None | str | Unset): Filter by assignee username/email
        reporter (None | str | Unset): Filter by reporter username/email
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        status=status,
        assignee=assignee,
        reporter=reporter,
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
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    status: None | TicketStatus | Unset = UNSET,
    assignee: None | str | Unset = UNSET,
    reporter: None | str | Unset = UNSET,
    x_user_id: str,
    x_project_key: str,
) -> HTTPValidationError | TicketListResponse | None:
    """List tickets with filtering

     List tickets with optional filtering and pagination.

    All filter parameters are optional. Results are paginated using limit/offset.

    Args:
        limit (int | Unset): Maximum number of tickets to return Default: 100.
        offset (int | Unset): Number of tickets to skip Default: 0.
        status (None | TicketStatus | Unset): Filter by ticket status
        assignee (None | str | Unset): Filter by assignee username/email
        reporter (None | str | Unset): Filter by reporter username/email
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketListResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        offset=offset,
        status=status,
        assignee=assignee,
        reporter=reporter,
        x_user_id=x_user_id,
        x_project_key=x_project_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    status: None | TicketStatus | Unset = UNSET,
    assignee: None | str | Unset = UNSET,
    reporter: None | str | Unset = UNSET,
    x_user_id: str,
    x_project_key: str,
) -> Response[HTTPValidationError | TicketListResponse]:
    """List tickets with filtering

     List tickets with optional filtering and pagination.

    All filter parameters are optional. Results are paginated using limit/offset.

    Args:
        limit (int | Unset): Maximum number of tickets to return Default: 100.
        offset (int | Unset): Number of tickets to skip Default: 0.
        status (None | TicketStatus | Unset): Filter by ticket status
        assignee (None | str | Unset): Filter by assignee username/email
        reporter (None | str | Unset): Filter by reporter username/email
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TicketListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        status=status,
        assignee=assignee,
        reporter=reporter,
        x_user_id=x_user_id,
        x_project_key=x_project_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
    status: None | TicketStatus | Unset = UNSET,
    assignee: None | str | Unset = UNSET,
    reporter: None | str | Unset = UNSET,
    x_user_id: str,
    x_project_key: str,
) -> HTTPValidationError | TicketListResponse | None:
    """List tickets with filtering

     List tickets with optional filtering and pagination.

    All filter parameters are optional. Results are paginated using limit/offset.

    Args:
        limit (int | Unset): Maximum number of tickets to return Default: 100.
        offset (int | Unset): Number of tickets to skip Default: 0.
        status (None | TicketStatus | Unset): Filter by ticket status
        assignee (None | str | Unset): Filter by assignee username/email
        reporter (None | str | Unset): Filter by reporter username/email
        x_user_id (str): User ID for authentication
        x_project_key (str): Jira project key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TicketListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            offset=offset,
            status=status,
            assignee=assignee,
            reporter=reporter,
            x_user_id=x_user_id,
            x_project_key=x_project_key,
        )
    ).parsed
