"""Authentication module for Alation MCP Server."""

import os
from typing import Optional, Union

from alation_ai_agent_sdk import (
    UserAccountAuthParams,
    ServiceAccountAuthParams,
    csv_str_to_tool_list,
)


def get_auth_params() -> tuple[str, Union[UserAccountAuthParams, ServiceAccountAuthParams]]:
    """
    Load authentication parameters from environment variables.

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
