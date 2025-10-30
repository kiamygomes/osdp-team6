from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.oauth_callback_api_v1_auth_callback_get_response_oauth_callback_api_v1_auth_callback_get import (
    OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet,
)
from ...types import UNSET, Response


def _get_kwargs(
    *,
    code: str,
    state: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["code"] = code

    params["state"] = state

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/auth/callback",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet | None:
    if response.status_code == 200:
        response_200 = OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet.from_dict(
            response.json()
        )

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
) -> Response[HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    code: str,
    state: str,
) -> Response[HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet]:
    """OAuth 2.0 callback endpoint

     Handle the OAuth 2.0 callback from Jira.

    This endpoint receives the authorization code, exchanges it for tokens,
    and stores them for the user. Returns the user_id to use in subsequent requests.

    Args:
        code (str): Authorization code from Jira
        state (str): State for CSRF protection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet]
    """

    kwargs = _get_kwargs(
        code=code,
        state=state,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    code: str,
    state: str,
) -> HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet | None:
    """OAuth 2.0 callback endpoint

     Handle the OAuth 2.0 callback from Jira.

    This endpoint receives the authorization code, exchanges it for tokens,
    and stores them for the user. Returns the user_id to use in subsequent requests.

    Args:
        code (str): Authorization code from Jira
        state (str): State for CSRF protection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet
    """

    return sync_detailed(
        client=client,
        code=code,
        state=state,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    code: str,
    state: str,
) -> Response[HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet]:
    """OAuth 2.0 callback endpoint

     Handle the OAuth 2.0 callback from Jira.

    This endpoint receives the authorization code, exchanges it for tokens,
    and stores them for the user. Returns the user_id to use in subsequent requests.

    Args:
        code (str): Authorization code from Jira
        state (str): State for CSRF protection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet]
    """

    kwargs = _get_kwargs(
        code=code,
        state=state,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    code: str,
    state: str,
) -> HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet | None:
    """OAuth 2.0 callback endpoint

     Handle the OAuth 2.0 callback from Jira.

    This endpoint receives the authorization code, exchanges it for tokens,
    and stores them for the user. Returns the user_id to use in subsequent requests.

    Args:
        code (str): Authorization code from Jira
        state (str): State for CSRF protection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OauthCallbackApiV1AuthCallbackGetResponseOauthCallbackApiV1AuthCallbackGet
    """

    return (
        await asyncio_detailed(
            client=client,
            code=code,
            state=state,
        )
    ).parsed
