"""
Authentication module for Alation MCP Server.

This module provides authentication functionality for both STDIO and HTTP modes:

- AlationTokenVerifier: Validates OAuth tokens against Alation's userinfo endpoint
- get_auth_params(): Loads authentication configuration from environment variables

STDIO Mode Authentication:
- Uses environment variables for user_account or service_account authentication
- Tokens are managed by the AlationAIAgentSDK directly

HTTP Mode Authentication:
- Validates incoming Bearer tokens via AlationTokenVerifier
- Integrates with FastMCP's authentication middleware
- Per-request token validation and user identification

Environment Variables Required:
- ALATION_AUTH_METHOD: "user_account" or "service_account"
- For user_account: ALATION_USER_ID, ALATION_REFRESH_TOKEN
- For service_account: ALATION_CLIENT_ID, ALATION_CLIENT_SECRET
"""

import os
import time
import logging
from typing import Union

import httpx
from mcp.server.auth.provider import AccessToken, TokenVerifier

from alation_ai_agent_sdk import UserAccountAuthParams, ServiceAccountAuthParams


class AlationTokenVerifier(TokenVerifier):
    """Token verifier for Alation OAuth authentication."""

    # TODO: this logic works for opaque token, but if JWT is enabled, we need to use the /introspect flow

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify OAuth token with Alation userinfo endpoint."""
        userinfo_url = f"{self.base_url}/integration/v1/userinfo/"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(userinfo_url, headers=headers)
                if response.status_code == 200:
                    userinfo = response.json()
                    return AccessToken(
                        token=token,
                        client_id=str(userinfo.get("id", "alation_client_id")),
                        scopes=[userinfo.get("role", "openid")],
                        expires_at=int(time.time()) + 3600,
                    )
                else:
                    logging.warning(f"Token verification failed with status {response.status_code}")
                    return None
            except Exception as e:
                logging.error(f"Error verifying token: {e}")
                return None


def get_auth_params() -> tuple[str, Union[UserAccountAuthParams, ServiceAccountAuthParams]]:
    """
    Load authentication parameters from environment variables.

    Required Environment Variables:
    - ALATION_AUTH_METHOD: "user_account" or "service_account"

    For user_account method:
    - ALATION_USER_ID: Integer user ID
    - ALATION_REFRESH_TOKEN: User's refresh token

    For service_account method:
    - ALATION_CLIENT_ID: Service account client ID
    - ALATION_CLIENT_SECRET: Service account client secret

    Returns:
        tuple: (auth_method, auth_params)

    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    auth_method = os.getenv("ALATION_AUTH_METHOD")

    if not auth_method:
        raise ValueError("Missing required environment variable: ALATION_AUTH_METHOD")

    if auth_method == "user_account":
        user_id = os.getenv("ALATION_USER_ID")
        refresh_token = os.getenv("ALATION_REFRESH_TOKEN")
        if not user_id or not refresh_token:
            raise ValueError(
                "Missing required environment variables: ALATION_USER_ID and ALATION_REFRESH_TOKEN for 'user_account' auth_method"
            )
        try:
            user_id = int(user_id)
        except ValueError:
            raise ValueError("ALATION_USER_ID must be an integer.")
        auth_params = UserAccountAuthParams(user_id, refresh_token)

    elif auth_method == "service_account":
        client_id = os.getenv("ALATION_CLIENT_ID")
        client_secret = os.getenv("ALATION_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError(
                "Missing required environment variables: ALATION_CLIENT_ID and ALATION_CLIENT_SECRET for 'service_account' auth_method"
            )
        auth_params = ServiceAccountAuthParams(client_id, client_secret)

    else:
        raise ValueError(
            "Invalid ALATION_AUTH_METHOD. Must be 'user_account' or 'service_account'."
        )

    return auth_method, auth_params
