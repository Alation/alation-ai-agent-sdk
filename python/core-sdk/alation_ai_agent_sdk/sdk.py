from typing import Dict, Any, Optional
from http import HTTPStatus  # Added for HTTPStatus.BAD_REQUEST

from .api import AlationAPI, AlationAPIError
from .tools import AlationContextTool


class AlationAIAgentSDK:
    """
    SDK for interacting with Alation AI Agent capabilities.

    Can be initialized using one of two authentication methods:
    1. User ID and Refresh Token:
       sdk = AlationAIAgentSDK(base_url="https://company.alationcloud.com", user_id=123, refresh_token="your_refresh_token")
    2. Service Account (Client ID and Client Secret):
       sdk = AlationAIAgentSDK(base_url="https://company.alationcloud.com", client_id="your_client_id", client_secret="your_client_secret")

    If both sets of credentials are provided, Client ID and Client Secret will be used by default.
    """

    def __init__(
        self,
        base_url: str,
        user_id: Optional[int] = None,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string.")

        # Determine authentication method, prioritizing service account if both are provided
        is_service_account_auth = client_id is not None and client_secret is not None
        is_refresh_token_auth = user_id is not None and refresh_token is not None

        if is_service_account_auth:
            # Use service account credentials
            if not client_id or not isinstance(client_id, str):
                raise ValueError(
                    "client_id must be a non-empty string for service account authentication."
                )
            if not client_secret or not isinstance(client_secret, str):
                raise ValueError(
                    "client_secret must be a non-empty string for service account authentication."
                )
            self.auth_params = {"client_id": client_id, "client_secret": client_secret}
            if is_refresh_token_auth:
                pass
        elif is_refresh_token_auth:
            if not isinstance(user_id, int):
                raise ValueError("user_id must be an integer for refresh token authentication.")
            if not refresh_token or not isinstance(refresh_token, str):
                raise ValueError("refresh_token must be a non-empty string")
            self.auth_params = {"user_id": user_id, "refresh_token": refresh_token}
        else:
            raise ValueError(
                "Missing authentication credentials. Provide either (user_id and refresh_token) or (client_id and client_secret)."
            )

        self.api = AlationAPI(base_url=base_url, **self.auth_params)
        self.context_tool = AlationContextTool(self.api)

    def get_context(
        self, question: str, signature: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch context from Alation's catalog for a given question and signature.

        Returns either:
        - JSON context result (dict)
        - Error object with keys: message, reason, resolution_hint, response_body
        """
        try:
            return self.api.get_context_from_catalog(question, signature)
        except AlationAPIError as e:
            return {"error": e.to_dict()}

    def get_tools(self):
        return [self.context_tool]
