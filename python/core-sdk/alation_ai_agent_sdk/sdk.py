from typing import Dict, Any, Optional

from .api import AlationAPI, AlationAPIError
from .tools import AlationContextTool


class AlationAIAgentSDK:
    def __init__(self, base_url: str, user_id: int, refresh_token: str):
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string.")
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer.")
        if not refresh_token or not isinstance(refresh_token, str):
            raise ValueError("refresh_token must be a non-empty string.")

        self.api = AlationAPI(base_url, user_id, refresh_token)
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
