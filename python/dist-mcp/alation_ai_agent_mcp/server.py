import os
import secrets
import json
from http import HTTPStatus
from typing import Dict, Any

from mcp.server.auth.provider import OAuthAuthorizationServerProvider, AccessToken
from mcp.server.fastmcp import FastMCP
from alation_ai_agent_sdk import AlationAIAgentSDK, UserAccountAuthParams, ServiceAccountAuthParams
from mcp.shared._httpx_utils import create_mcp_http_client


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AlationOAuthProvider(OAuthAuthorizationServerProvider):
    def __init__(self, client_id: str, client_secret: str, auth_url: str, token_url: str, callback_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.callback_url = callback_url
        self.auth_codes = {}
        self.tokens = {}

    async def authorize(self, client_id: str, redirect_uri: str, state: str) -> str:
        state = state or secrets.token_hex(16)
        auth_url = (
            f"{self.auth_url}?client_id={self.client_id}&redirect_uri={self.callback_url}&state={state}"
        )
        return auth_url

    async def handle_callback(self, code: str, state: str) -> str:
        async with create_mcp_http_client() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.callback_url,
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                raise HTTPException(400, "Failed to exchange code for token")

            data = response.json()
            if "error" in data:
                raise HTTPException(400, data.get("error_description", data["error"]))

            access_token = data["access_token"]
            self.tokens[state] = AccessToken(token=access_token, client_id=self.client_id, scopes=[], expires_at=None)
            return access_token

    async def load_access_token(self, token: str) -> AccessToken | None:
        return self.tokens.get(token)


def create_server():
    # Load Alation credentials from environment variables
    base_url = os.getenv("ALATION_BASE_URL")
    auth_method = os.getenv("ALATION_AUTH_METHOD")
    client_id = os.getenv("ALATION_CLIENT_ID")
    client_secret = os.getenv("ALATION_CLIENT_SECRET")
    auth_url = os.getenv("ALATION_AUTH_URL")
    token_url = os.getenv("ALATION_TOKEN_URL")
    callback_url = os.getenv("ALATION_CALLBACK_URL")

    if not base_url or not auth_method:
        raise ValueError(
            "Missing required environment variables: ALATION_BASE_URL and ALATION_AUTH_METHOD"
        )

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

    elif auth_method == "oauth":
        if not all([client_id, client_secret, auth_url, token_url, callback_url]):
            raise ValueError("Missing required environment variables for OAuth setup")

        oauth_provider = AlationOAuthProvider(client_id, client_secret, auth_url, token_url, callback_url)

        @mcp.custom_route("/oauth/callback", methods=["GET"])
        async def oauth_callback_handler(request):
            code = request.query_params.get("code")
            state = request.query_params.get("state")

            if not code or not state:
                raise HTTPException(HTTPStatus.BAD_REQUEST, "Missing code or state parameter")

            try:
                access_token = await oauth_provider.handle_callback(code, state)
                return mcp.response(json.dumps({"access_token": access_token}), status=HTTPStatus.OK)
            except HTTPException as e:
                return mcp.response(json.dumps({"error": e.detail}), status=e.status_code)
            except Exception as e:
                return mcp.response(json.dumps({"error": "server_error", "error_description": str(e)}), status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # Initialize FastMCP server
    mcp = FastMCP(name="Alation MCP Server", version="0.1.0")

    # Initialize Alation SDK
    alation_sdk = AlationAIAgentSDK(base_url, auth_method, auth_params)

    @mcp.tool(name=alation_sdk.context_tool.name, description=alation_sdk.context_tool.description)
    def alation_context(question: str, signature: Dict[str, Any] | None = None) -> str:
        result = alation_sdk.get_context(question, signature)
        return str(result)

    return mcp


# Delay server instantiation
mcp = None


def run_server():
    """Entry point for running the MCP server"""
    global mcp
    mcp = create_server()
    mcp.run()


if __name__ == "__main__":
    run_server()
