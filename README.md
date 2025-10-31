# Alation AI Agent SDK

The Alation AI Agent SDK enables AI agents to access and leverage metadata from the Alation Data Catalog.

## Overview

This SDK empowers AI agents to:

- Easily integrate with Alation's Data Catalog
- Address use cases like Asset Curation, Search & Discovery, Role Based Agents, and Data Analyst Agents
- Use natural language to search for relevant metadata
- Integrate seamlessly with AI frameworks like MCP

## Components

The project is organized into multiple components:

- **Core SDK** - Foundation with API client and context tools
- **MCP Integration** - Server implementation for Model Context Protocol
- **LangChain Integration** - Adapters for the LangChain framework


### Core SDK (`alation-ai-agent-sdk`)

The core SDK provides the foundation for interacting with the Alation API. It handles authentication, request formatting, and response parsing.

[Learn more about the Core SDK](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/core-sdk/)

### LangChain Integration (`alation-ai-agent-langchain`)

This component integrates the SDK with the LangChain framework, enabling the creation of sophisticated AI agents that can reason about your data catalog.

[Learn more about the LangChain Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/)

### MCP Integration (`alation-ai-agent-mcp`)

The MCP integration provides an MCP-compatible server that exposes Alation's context capabilities to any MCP client. Supports both traditional STDIO mode for direct MCP client connections and HTTP mode for web applications and API integrations.

[Learn more about the MCP Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-mcp/)

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).

### Installation

```bash
# Install core SDK
pip install alation-ai-agent-sdk

# Install LangChain integration
pip install alation-ai-agent-langchain

# Install MCP integration
pip install alation-ai-agent-mcp
```

## Usage

The library needs to be configured with your Alation instance credentials. You should use `ServiceAccountAuthParams`.


### Service Account Authentication (Recommended)
```python
from alation_ai_agent_sdk import AlationAPI, ServiceAccountAuthParams

# Initialize the SDK with Service Account Authentication
auth_params = ServiceAccountAuthParams(
    client_id="your_client_id",
    client_secret="your_client_secret"
)
alation_api = AlationAPI(
    base_url="https://your-alation-instance.com",
    auth_method="service_account",
    auth_params=auth_params
)
```

If you cannot obtain service account credentials (admin only), see the [User Account Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md#user-account-authentication) for instructions.

## Supported Tools

- [alation_context](guides/tools/alation_context.md)
- [bulk_retrieval](guides/tools/bulk_retrieval.md)
- [check_job_status](guides/tools/check_job_status.md)
- [data_quality_tool](guides/tools/data_quality_tool.md)
- [get_custom_fields_definitions](guides/tools/get_custom_fields_definitions.md)
- [get_data_products](guides/tools/get_data_products.md)
- [get_data_sources_tool](guides/tools/get_data_sources_tool.md)
- [get_signature_creation_instructions](guides/tools/get_signature_creation_instructions.md)
- [lineage](guides/tools/lineage.md)
- [update_catalog_asset_metadata](guides/tools/update_catalog_asset_metadata.md)

## Supported Agents

- [catalog_context_search_agent](guides/agents/catalog_context_search_agent.md)
- [custom_agent](guides/agents/custom_agent.md)
- [query_flow_agent](guides/agents/query_flow_agent.md)
- [sql_query_agent](guides/agents/sql_query_agent.md)

## Shape the SDK to your needs

The SDK's `alation-context` and `bulk_retrieval` tools support customizing response content using signatures. This powerful feature allows you to specify which fields to include and how to filter the catalog results. For instance:

```python
# Define a signature for searching only tables that optionally
# include joins and filters if relevant to the user question
signature = {
    "table": {
        "fields_required": ["name", "title", "description"],
        "fields_optional": ["common_joins", "common_filters"]
    }
}

# Use the signature with your query
response = sdk.get_context(
    "What are our sales tables?",
    signature
)
```

For more information about signatures, refer to
<a href="https://developer.alation.com/dev/docs/customize-the-aggregated-context-api-calls-with-a-signature" target="blank"> Using Signatures </a>

## Guides and Example Agents

### General
- [Authentication](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/authentication.md) - How to get access.
- [Tool Management](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/tool_management.md) - Controls for enabling or disabling specific tools.

#### Aggregated Context / Bulk Retrieval Tool
- [Planning an Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/planning.md) - Practical considerations for getting the most out of your agents and the Alation Data Catalog.
- <a href="https://developer.alation.com/dev/docs/customize-the-aggregated-context-api-calls-with-a-signature" target="blank"> Using Signatures </a> - How to customize your agent with concrete examples.
- <a href="https://developer.alation.com/dev/docs/guide-to-aggregated-context-api-beta#supported-object-types-and-default-object-type-fields" target="blank">Supported Object Types and Default Object Fields</a> - See which objects are supported.
- <a href="https://developer.alation.com/dev/docs/customize-the-aggregated-context-api-calls-with-a-signature#supported-object-fields" target="blank">Supported Object Fields</a> - A comprehensive reference for each supported object.

#### Other Tools
- [Data Quality: Check SQL Query](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/tools/data_quality_tool.md) - Identifies data quality issues within a SQL query.
- [Lineage](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/tools/lineage.md) - Resolve upstream and downstream graphs.


### Core SDK

Direct usage examples for the Alation AI Agent SDK:
- [Basic Usage Example](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/core-sdk/examples/basic_usage/) - Simple example showing SDK initialization and context queries.
- [QA Chatbot Example](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/core-sdk/examples/qa_chatbot/) - Interactive chatbot demonstrating conversation context and signature usage.

### Model Context Protocol (MCP)

Enable agentic experiences with the Alation Data Catalog.

- [MCP Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/) - Getting the Alation MCP server up and running.
- [Integration with Code Editors](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/code_editors.md) - Use the tools directly in your code editor.
- [Testing with MCP Inspector](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/testing_with_mcp_inspector.md) - Steps for debugging and verification.
- [Claude Desktop Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/claude_desktop.md) - Leverage the Alation MCP server within Claude Desktop.
- [LibreChat Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/librechat.md) - Create assistants and agents alike.

### LangChain

Harness the SDK to build complex agents and workflows.
- [LangChain Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/) - How to integrate the SDK into your LangChain agents.
- [Basic Usage Example](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/examples/basic_usage/) - A simple example.
- [Multi Agent Example](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/examples/multi_agent_return_eligibility/) - A multi agent workflow with several SDK integration points.

## Integrating with other toolkits

The number of published agent frameworks and toolkits appears to be increasing every day. If you don't happen to see the framework or toolkit you're using here, it's still possible to adapt `alation-ai-agent-sdk` to your needs. It may be as simple as writing a wrapping function where a decorator is applied.

While we want to reach as many developers as possible and make it as convenient as possible, we anticipate a long tail distribution of toolkits and won't be able to write adapters for every case. If you'd like support for a specific toolkit, please [create an issue](https://github.com/Alation/alation-ai-agent-sdk/issues) to discuss.




