"""
Authentication module for Alation MCP Server.

This module provides authentication functionality for both STDIO and HTTP modes:

- AlationTokenVerifier: Validates OAuth tokens against Alation's userinfo endpoint
- get_stdio_auth_params(): Loads authentication configuration from environment variables

STDIO Mode Authentication:
- Uses environment variables for user_account or service_account authentication
- Tokens are managed by the AlationAIAgentSDK directly

HTTP Mode Authentication:
- Validates incoming Bearer tokens via AlationTokenVerifier
- Integrates with FastMCP's authentication middleware
- Per-request token validation and user identification

Environment Variables:

Required (STDIO mode only):
- ALATION_BASE_URL: Base URL of your Alation instance (e.g., "https://company.alationcloud.com")
- ALATION_AUTH_METHOD: "service_account"

For service_account authentication:
- ALATION_CLIENT_ID: OAuth client ID (required)
- ALATION_CLIENT_SECRET: OAuth client secret (required)

Optional configuration:
- ALATION_DISABLED_TOOLS: Comma-separated list of tools to disable
- ALATION_ENABLED_BETA_TOOLS: Comma-separated list of beta tools to enable
- MCP_EXTERNAL_URL: External URL for HTTP mode load balancer support

Note: HTTP mode uses OAuth headers instead of authentication environment variables
"""

import os
import time
import logging

import httpx
from fastmcp.server.auth import AccessToken
from fastmcp.server.auth import TokenVerifier

from alation_ai_agent_sdk import ServiceAccountAuthParams


class AlationTokenVerifier(TokenVerifier):
    """Token verifier for Alation OAuth authentication."""

    # NOTE: this logic works for opaque token, but if JWT is enabled, we should consider
    # using the /introspect flow as it doesn't require the userinfo endpoint
    #
    # See if you can pass base_url value dynamically either from the JWT payload or header

    def __init__(
        self,
        base_url: str,
        token_verification: str = "opaque",
        userinfo_path: str = "/integration/v1/userinfo/",
        jwt_introspect_path: str = "/oauth/v2/introspect/",
    ) -> None:
        self.base_url = base_url
        self.token_verification = token_verification
        self.userinfo_path = userinfo_path
        self.jwt_introspect_path = jwt_introspect_path
        # Required by FastMCP RemoteAuthProvider
        # Neither auth modes require specific OAuth scopes
        self.required_scopes: list[str] = []

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify OAuth token with Alation userinfo endpoint."""
        userinfo_url = f"{self.base_url}{self.userinfo_path}"
        # TBD: Figure out how support multiple token_verification flows
        # - get client id and secret for introspection flow where possible
        # introspect_url = f"{self.base_url}{self.jwt_introspect_path}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=5.0) as client:
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
                elif response.status_code == 401:
                    logging.warning(
                        "Token verification failed: Invalid or expired token"
                    )
                    return None
                elif response.status_code == 403:
                    logging.warning(
                        "Token verification failed: Insufficient permissions"
                    )
                    return None
                elif response.status_code == 404:
                    logging.error(
                        f"Token verification failed: Userinfo endpoint not found at {userinfo_url}"
                    )
                    return None
                else:
                    logging.warning(
                        f"Token verification failed with status {response.status_code}: {response.text}"
                    )
                    return None
            except httpx.TimeoutException as e:
                logging.error(f"Token verification timed out after 5 seconds: {e}")
                return None
            except httpx.ConnectError as e:
                logging.error(
                    f"Failed to connect to Alation instance at {self.base_url}: {e}"
                )
                return None
            except httpx.RequestError as e:
                logging.error(f"Network error during token verification: {e}")
                return None
            except Exception as e:
                logging.error(f"Unexpected error verifying token: {e}")
                return None


def get_stdio_auth_params() -> tuple[str, ServiceAccountAuthParams]:
    """
    Load authentication parameters from environment variables.

    Required Environment Variables:
    - ALATION_AUTH_METHOD: "service_account"

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

    if auth_method == "service_account":
        client_id = os.getenv("ALATION_CLIENT_ID")
        client_secret = os.getenv("ALATION_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError(
                "Missing required environment variables: ALATION_CLIENT_ID and ALATION_CLIENT_SECRET for 'service_account' auth_method"
            )
        auth_params = ServiceAccountAuthParams(client_id, client_secret)

    else:
        raise ValueError(
            "Invalid ALATION_AUTH_METHOD. Must be 'service_account' for STDIO server"
        )

    return auth_method, auth_params
