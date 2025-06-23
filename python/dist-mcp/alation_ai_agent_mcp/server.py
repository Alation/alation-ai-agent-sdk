import os
from typing import Dict, Any, Annotated, Literal
from pydantic import Field

from mcp.server.fastmcp import FastMCP
from alation_ai_agent_sdk import AlationAIAgentSDK, UserAccountAuthParams, ServiceAccountAuthParams


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
    mcp = FastMCP(name="Alation MCP Server", version="0.3.0")

    # Initialize Alation SDK
    alation_sdk = AlationAIAgentSDK(base_url, auth_method, auth_params)

    @mcp.tool(name=alation_sdk.context_tool.name, description=alation_sdk.context_tool.description)
    def alation_context(
        question: Annotated[
            str, Field(description="The exact user question, unmodified and uninterpreted.")
        ],
        signature: Annotated[
            Dict[str, Any] | None,
            Field(
                description="A JSON specification of which fields to include in the response. Allows customizing the response format and content."
            ),
        ] = None,
    ) -> str:
        result = alation_sdk.get_context(question, signature)
        return str(result)

    @mcp.tool(
        name=alation_sdk.data_product_tool.name,
        description=alation_sdk.data_product_tool.description,
    )
    def get_data_products(
        product_id: Annotated[
            str | None, Field(description="Exact product identifier for fast direct retrieval.")
        ] = None,
        query: Annotated[
            str | None,
            Field(description="Natural language search query for discovery and exploration."),
        ] = None,
    ) -> str:
        result = alation_sdk.get_data_products(product_id, query)
        return str(result)

    @mcp.tool(
        name=alation_sdk.check_data_quality_tool.name,
        description=alation_sdk.check_data_quality_tool.description,
    )
    def check_data_quality(
        sql_query: Annotated[
            str | None, Field(description="SQL query to analyze for data quality checks.")
        ] = None,
        output_format: Annotated[
            Literal["json", "yaml_markdown"] | None,
            Field(description="Output format for results: 'json' or 'yaml_markdown'."),
        ] = None,
        table_ids: Annotated[
            list[int] | None,
            Field(
                description="List of table IDs to check (max 30). Use context tool to look up IDs."
            ),
        ] = None,
        db_uri: Annotated[
            str | None,
            Field(
                description="Database URI for the query, e.g., 'postgresql://user:pass@host/db'."
            ),
        ] = None,
        ds_id: Annotated[
            int | None, Field(description="Datasource ID for the query or tables.")
        ] = None,
        bypassed_dq_sources: Annotated[
            list[Literal["trust_flags", "open_data_quality", "native_data_quality"]] | None,
            Field(
                description="List of data quality sources to bypass. Allowed values: 'trust_flags', 'open_data_quality', 'native_data_quality'."
            ),
        ] = None,
        default_schema_name: Annotated[
            str | None,
            Field(description="Default schema name to use if not specified in the query."),
        ] = None,
        dq_score_threshold: Annotated[
            int | None, Field(description="Data quality score threshold for passing results.")
        ] = None,
    ) -> str:
        result = alation_sdk.check_data_quality(
            table_ids=table_ids,
            sql_query=sql_query,
            db_uri=db_uri,
            ds_id=ds_id,
            bypassed_dq_sources=bypassed_dq_sources,
            default_schema_name=default_schema_name,
            output_format=output_format,
            dq_score_threshold=dq_score_threshold,
        )
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
