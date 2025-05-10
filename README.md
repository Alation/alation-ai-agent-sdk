# Alation AI Agent SDK

The Alation AI Agent SDK enables AI agents to access and leverage metadata from the Alation Data Catalog.

## Overview

This SDK empowers AI agents to:

- Retrieve contextual information from Alation's data catalog
- Use natural language to search for relevant metadata
- Customize response formats using flexible signature specifications
- Integrate seamlessly with AI frameworks like Langchain and MCP

## Components

The project is organized into multiple components:

- **Core SDK** - Foundation with API client and context tools
- **Langchain Integration** - Adapters for the Langchain framework
- **MCP Integration** - Server implementation for Model Completion Protocol

### Core SDK (`alation-ai-agent-sdk`)

The core SDK provides the foundation for interacting with the Alation API. It handles authentication, request formatting, and response parsing.

[Learn more about the Core SDK](python/core-sdk/README.md)

### Langchain Integration (`alation-ai-agent-langchain`)

This component integrates the SDK with the Langchain framework, enabling the creation of sophisticated AI agents that can reason about your data catalog.

[Learn more about the Langchain Integration](python/dist-langchain/README.md)

### MCP Integration (`alation-ai-agent-mcp`)

The MCP integration provides an MCP-compatible server that exposes Alation's context capabilities to any MCP client.

[Learn more about the MCP Integration](python/dist-mcp/README.md)

## Getting Started

### Installation

```bash
# Install core SDK
pip install alation-ai-agent-sdk

# Install Langchain integration
pip install alation-ai-agent-langchain

# Install MCP integration
pip install alation-ai-agent-mcp
```

### Prerequisites

To use the SDK, you'll need:

- Python 3.10 or higher
- A valid API Access Token created on your Alation Data Catalog instance

## Working with Signatures

The SDK supports customizing the response format and content using signatures. This powerful feature allows you to specify which fields to include and how to filter the results:

```python
# Define a signature for tables with column details
signature = {
    "table": {
        "fields_required": ["name", "title", "description"],
        "fields_optional": ["common_joins", "common_filters"],
        "child_objects": {
            "columns": {
                "fields": ["name", "data_type", "description"]
            }
        }
    }
}

# Use the signature with your query
response = sdk.get_context("What are our sales tables?", signature)
```

For more information about signatures, refer to the [Signature Documentation](guides/signature.md).

## Usage

The library needs to be configured with your Alation instance credentials:

```python
from alation_ai_agent_sdk import AlationAIAgentSDK

alation_ai_sdk = AlationAIAgentSDK(
    base_url="https://your-alation-instance.com",
    user_id=12345,  # Your numeric user ID
    refresh_token="your_refresh_token"
)
```

## Supported Tools

### alation_context

An AI-powered tool that retrieves contextual information from the Alation catalog based on natural language queries.

**Functionality:**
- Accepts user questions in natural language
- Performs query rewrites to optimize search results
- Returns relevant catalog data in JSON format
- Can return multiple object types in a single response

**Usage:**
```python
response = alation_ai_sdk.get_context("What certified data set is used to make decisions on providing credit for customers?")
```

**Input Parameters:**
- `question` (string): The natural language query

**Returns:**
- JSON-formatted response containing relevant catalog information

## Supported Object Types and Fields

The SDK currently supports the following object types and fields:

| Object Type | Fields |
-------------|--------|
| **Schema** | name, title, description, url |
| **Table** | name, title, description, url, common_joins*, common_filters*, columns* |
| **Column** | name, title, data_type, url, description*, sample_values* |
| **Documentation** (Includes Document, Article, Glossary, and Document Folder) | title, content, url |
| **Query** | title, description, content, url |

### Child Object Relationships

| Child Object | Parent Object | Fields |
|--------------|---------------|--------|
| **columns** | table | name, title, data_type, url*, description*, sample_values* |

*Note: Fields marked with * are optional fields.*

## LangChain Integration

The SDK seamlessly integrates with LangChain, allowing you to use Alation's context as tools within LangChain agents and chains.

### Basic Usage

```python
from alation_ai_agent_langchain import AlationAIAgentSDK, get_langchain_tools
from langchain.agents import AgentExecutor, create_structured_chat_agent

# Initialize the SDK
alation_ai_sdk = AlationAIAgentSDK(
    base_url="https://your-alation-instance.com",
    user_id=12345,
    refresh_token="your_refresh_token"
)

# Use the helper function
tools = get_langchain_tools(alation_ai_sdk)

# Create and run an agent
agent = create_structured_chat_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
response = agent_executor.run("What are the main sales tables in our data warehouse?")
```

For more advanced LangChain integration patterns and examples, see our [LangChain Integration Guide](./guides/langchain/)

## Model Context Protocol (MCP) Integration

The SDK includes built-in support for the Model Context Protocol (MCP), which enables AI models to retrieve knowledge from Alation during inference.

### Quick Start

```bash
# Set required environment variables
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_USER_ID="123456"  # Your numeric user ID
export ALATION_REFRESH_TOKEN="your-refresh-token"

# Run the MCP server
python -m alation_ai_agent_mcp.server
```
Note: Running this command only starts the MCP server - you won't be able to ask questions directly. The server needs to be connected to an MCP client (like Claude Desktop or LibreChat) or tested with the MCP Inspector tool. See the guides below for details on connecting to clients.

For detailed MCP integration instructions, see:
- [Testing with MCP Inspector](./guides/mcp/testing_with_mcp_inspector.md) - Validate your setup
- [Claude Desktop Integration](./guides/mcp/claude_desktop.md) - Connect to Claude Desktop
- [LibreChat Integration](./guides/mcp/librechat.md) - Use with LibreChat **(Coming Soon)**

## Environment Variables

When using the MCP server, you'll need to configure the following:

- **ALATION_BASE_URL** - The URL of your Alation instance
- **ALATION_USER_ID** - Your numeric user ID in Alation
- **ALATION_REFRESH_TOKEN** - Your refresh token for Alation authentication
