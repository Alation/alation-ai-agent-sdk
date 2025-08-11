import os
from alation_ai_agent_sdk import (
    UserAccountAuthParams,
    ServiceAccountAuthParams,
    BearerTokenAuthParams,
)
from alation_ai_agent_sdk.api import CatalogAssetMetadataPayloadItem
from alation_ai_agent_sdk.tools import (
    AlationContextTool,
    AlationBulkRetrievalTool,
    GetDataProductTool,
    UpdateCatalogAssetMetadataTool,
    CheckJobStatusTool,
)
from alation_ai_agent_sdk import AlationAIAgentSDK

from mcp.server.fastmcp import Context


def load_env_credentials():
    """Load Alation credentials from environment variables."""
    base_url = os.getenv("ALATION_BASE_URL")
    auth_method = os.getenv("ALATION_AUTH_METHOD")

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

    else:
        raise ValueError(
            "Invalid ALATION_AUTH_METHOD. Must be 'user_account' or 'service_account'."
        )

    return base_url, auth_method, auth_params


# NOTE: To reliably access authentication details (scopes, claims), use the
# request.user object. The MCP framework's middleware attaches an 'AuthenticatedUser'
# to the underlying request, not the top-level Context, making this the official
# and intended access pattern.
#
# This is confirmed by reviewing the foundational repositories:
# - jlowin/fastmcp, PR #1 & #2: Establish that auth is attached to the request
#   and the request is then exposed to the context.
# - modelcontextprotocol/python-sdk, Issue #431: Shows community precedent for
#   using this pattern.
#
# user = ctx.request_context.request.user


def get_user_token_and_scope(ctx: Context):
    user = getattr(getattr(ctx, "request_context", None), "request", None)
    if user and hasattr(user, "user"):
        user_obj = user.user
        token = getattr(getattr(user_obj, "access_token", None), "token", None)
        scope = getattr(user_obj, "role", "openid")
        if not token or not isinstance(token, str):
            raise ValueError("Authenticated user token not found or not a string.")
        return token, scope
    raise ValueError("Authenticated user or token not found in context.")


def register_tools(mcp, base_url):
    """Register tools with the MCP server using static metadata and context-based SDK instantiation."""

    @mcp.tool(
        name=AlationContextTool._get_name(), description=AlationContextTool._get_description()
    )
    def alation_context(question: str, ctx: Context, signature: dict | None = None) -> str:
        token, scope = get_user_token_and_scope(ctx)
        alation_sdk = AlationAIAgentSDK(
            base_url=base_url,
            auth_method="bearer_token",
            auth_params=BearerTokenAuthParams(token=token),
        )
        result = alation_sdk.get_context(question, signature)
        return str(result)

    @mcp.tool(
        name=AlationBulkRetrievalTool._get_name(),
        description=AlationBulkRetrievalTool._get_description(),
    )
    def alation_bulk_retrieval(signature: dict, ctx: Context) -> str:
        token, _ = get_user_token_and_scope(ctx)
        alation_sdk = AlationAIAgentSDK(
            base_url=base_url,
            auth_method="bearer_token",
            auth_params=BearerTokenAuthParams(token=token),
        )
        result = alation_sdk.get_bulk_objects(signature)
        return str(result)

    @mcp.tool(
        name=GetDataProductTool._get_name(), description=GetDataProductTool._get_description()
    )
    def get_data_products(
        ctx: Context,
        product_id: str | None = None,
        query: str | None = None,
    ) -> str:
        token, _ = get_user_token_and_scope(ctx)
        alation_sdk = AlationAIAgentSDK(
            base_url=base_url,
            auth_method="bearer_token",
            auth_params=BearerTokenAuthParams(token=token),
        )
        result = alation_sdk.get_data_products(product_id, query)
        return str(result)

    @mcp.tool(
        name="update_catalog_asset_metadata",
        description=UpdateCatalogAssetMetadataTool._get_description(),
    )
    def update_catalog_asset_metadata(
        custom_field_values: list[CatalogAssetMetadataPayloadItem], ctx: Context
    ) -> str:
        token, _ = get_user_token_and_scope(ctx)
        alation_sdk = AlationAIAgentSDK(
            base_url=base_url,
            auth_method="bearer_token",
            auth_params=BearerTokenAuthParams(token=token),
        )
        result = alation_sdk.update_catalog_asset_metadata(custom_field_values)
        return str(result)

    @mcp.tool(name="check_job_status", description=CheckJobStatusTool._get_description())
    def check_job_status(job_id: int, ctx: Context) -> str:
        token, _ = get_user_token_and_scope(ctx)
        alation_sdk = AlationAIAgentSDK(
            base_url=base_url,
            auth_method="bearer_token",
            auth_params=BearerTokenAuthParams(token=token),
        )
        result = alation_sdk.check_job_status(job_id)
        return str(result)
