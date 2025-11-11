from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_status_api_v1_auth_status_get_response_auth_status_api_v1_auth_status_get import (
    AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    user_id: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["user_id"] = user_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/auth/status",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet.from_dict(response.json())

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
) -> Response[AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    user_id: str,
) -> Response[AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError]:
    """Check authentication status

     Check if a user has valid OAuth tokens stored.

    Returns whether the user is authenticated and when tokens expire.

    Args:
        user_id (str): User ID to check

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    user_id: str,
) -> AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError | None:
    """Check authentication status

     Check if a user has valid OAuth tokens stored.

    Returns whether the user is authenticated and when tokens expire.

    Args:
        user_id (str): User ID to check

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        user_id=user_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    user_id: str,
) -> Response[AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError]:
    """Check authentication status

     Check if a user has valid OAuth tokens stored.

    Returns whether the user is authenticated and when tokens expire.

    Args:
        user_id (str): User ID to check

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    user_id: str,
) -> AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError | None:
    """Check authentication status

     Check if a user has valid OAuth tokens stored.

    Returns whether the user is authenticated and when tokens expire.

    Args:
        user_id (str): User ID to check

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthStatusApiV1AuthStatusGetResponseAuthStatusApiV1AuthStatusGet | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            user_id=user_id,
        )
    ).parsed
