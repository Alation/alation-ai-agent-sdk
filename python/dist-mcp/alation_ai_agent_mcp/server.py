import os
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP
from alation_ai_agent_sdk import AlationAIAgentSDK, UserAccountAuthParams, ServiceAccountAuthParams
from alation_ai_agent_sdk.api import CatalogAssetMetadataPayloadItem

import logging

logger = logging.getLogger("alation.mcp.server")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

MCP_SERVER_VERSION = "0.5.0"


def create_server():
    # Load Alation credentials from environment variables
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

    # Initialize FastMCP server
    mcp = FastMCP(name="Alation MCP Server", version=MCP_SERVER_VERSION)

    alation_sdk = AlationAIAgentSDK(
        base_url, auth_method, auth_params, dist_version=f"mcp-{MCP_SERVER_VERSION}"
    )

    is_cloud = getattr(alation_sdk.api, "is_cloud", None)
    if is_cloud is None:
        raise RuntimeError(
            "Failed to fetch license info. Unable to determine if the instance is cloud or on-prem."
        )
    if not is_cloud:
        raise RuntimeError("This Alation instance is on-prem. MCP tools require a cloud instance.")

    alation_version = getattr(alation_sdk.api, "alation_release_name", None)
    is_cloud = getattr(alation_sdk.api, "is_cloud", None)
    logger.info(
        f"Alation MCP Server initializing |Alation version: {alation_version} | Cloud instance: {is_cloud} | dist_version: {f'mcp-{MCP_SERVER_VERSION}'}"
    )

    @mcp.tool(name=alation_sdk.context_tool.name, description=alation_sdk.context_tool.description)
    def alation_context(question: str, signature: Dict[str, Any] | None = None) -> str:
        result = alation_sdk.get_context(question, signature)
        return str(result)

    @mcp.tool(
        name=alation_sdk.bulk_retrieval_tool.name,
        description=alation_sdk.bulk_retrieval_tool.description,
    )
    def alation_bulk_retrieval(signature: Dict[str, Any]) -> str:
        result = alation_sdk.get_bulk_objects(signature)
        return str(result)

    @mcp.tool(
        name=alation_sdk.data_product_tool.name,
        description=alation_sdk.data_product_tool.description,
    )
    def get_data_products(product_id: Optional[str] = None, query: Optional[str] = None) -> str:
        result = alation_sdk.get_data_products(product_id, query)
        return str(result)

    @mcp.tool(
        name=alation_sdk.update_catalog_asset_metadata_tool.name,
        description=alation_sdk.update_catalog_asset_metadata_tool.description,
    )
    def update_catalog_asset_metadata(
        custom_field_values: list[CatalogAssetMetadataPayloadItem],
    ) -> str:
        result = alation_sdk.update_catalog_asset_metadata(custom_field_values)
        return str(result)

    @mcp.tool(
        name=alation_sdk.check_job_status_tool.name,
        description=alation_sdk.check_job_status_tool.description,
    )
    def check_job_status(job_id: int) -> str:
        result = alation_sdk.check_job_status(job_id)
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
