import uvicorn
import time
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl
from mcp.server.auth.provider import AccessToken, TokenVerifier
from alation_ai_agent_mcp.utils import register_tools


BASE_URL = "https://genai-gartner.mtse.alationcloud.com"


class AlationTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        userinfo_url = f"{BASE_URL}/integration/v1/userinfo/"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
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
                return None


def create_server(json_response: bool = False, transport: str = "http") -> FastMCP:
    auth = AuthSettings(
        issuer_url=AnyHttpUrl(BASE_URL),
        resource_server_url=AnyHttpUrl("http://localhost:8123"),
    )
    mcp = FastMCP(
        name="Alation MCP Server",
        json_response=json_response,
        auth=auth,
        token_verifier=AlationTokenVerifier(),
    )
    register_tools(mcp, BASE_URL)
    return mcp


def run_server():

    mcp = create_server(json_response=True, transport="http")
    uvicorn.run(mcp.streamable_http_app, host="localhost", port=8123)


if __name__ == "__main__":
    run_server()
