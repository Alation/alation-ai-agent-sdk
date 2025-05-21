from typing import Dict, Any, Optional
from http import HTTPStatus  # Added for HTTPStatus.BAD_REQUEST

from .api import AlationAPI, AlationAPIError
from .tools import AlationContextTool


class AlationAIAgentSDK:
    """
    SDK for interacting with Alation AI Agent capabilities.

    Can be initialized using one of two authentication methods:
    1. Refresh Token Authentication:
       sdk = AlationAIAgentSDK(base_url="https://company.alationcloud.com", auth_method="refresh_token", auth_params=(123, "your_refresh_token"))
    2. Service Account Authentication:
       sdk = AlationAIAgentSDK(base_url="https://company.alationcloud.com", auth_method="service_account", auth_params=("your_client_id", "your_client_secret"))
    """

    def __init__(
        self,
        base_url: str,
        auth_method: str,
        auth_params: tuple,
    ):
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string.")

        if not auth_method or not isinstance(auth_method, str):
            raise ValueError("auth_method must be a non-empty string.")

        if not isinstance(auth_params, tuple):
            raise ValueError("auth_params must be a tuple.")

        self.api = AlationAPI(base_url=base_url, auth_method=auth_method, auth_params=auth_params)
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
