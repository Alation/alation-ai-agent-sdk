# Alation AI Agent SDK

The Alation AI Agent SDK enables AI agents to access and leverage metadata from the Alation Data Catalog.

## Overview

This SDK empowers AI agents to:

- Retrieve contextual information from Alation's Data Catalog
- Use natural language to search for relevant metadata
- Customize response formats using flexible signature specifications
- Integrate seamlessly with AI frameworks like LangChain and MCP

## Components

The project is organized into multiple components:

- **Core SDK** - Foundation with API client and context tools
- **LangChain Integration** - Adapters for the LangChain framework
- **MCP Integration** - Server implementation for Model Context Protocol

### Core SDK (`alation-ai-agent-sdk`)

The core SDK provides the foundation for interacting with the Alation API. It handles authentication, request formatting, and response parsing.

[Learn more about the Core SDK](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/core-sdk/)

### LangChain Integration (`alation-ai-agent-langchain`)

This component integrates the SDK with the LangChain framework, enabling the creation of sophisticated AI agents that can reason about your data catalog.

[Learn more about the LangChain Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/)

### MCP Integration (`alation-ai-agent-mcp`)

The MCP integration provides an MCP-compatible server that exposes Alation's context capabilities to any MCP client.

[Learn more about the MCP Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-mcp/)

## Getting Started

### Installation

```bash
# Install core SDK
pip install alation-ai-agent-sdk

# Install LangChain integration
pip install alation-ai-agent-langchain

# Install MCP integration
pip install alation-ai-agent-mcp
```

### Prerequisites

To use the SDK, you'll need:

- Python 3.10 or higher
- A valid API Access Token created on your Alation Data Catalog instance

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

A retrieval tool that pulls contextual information from the Alation catalog based on natural language queries.

**Functionality**
- Accepts user questions in natural language
- Performs query rewrites to optimize search results
- Returns relevant catalog data in JSON format
- Can return multiple object types in a single response

**Usage**
```python
response = alation_ai_sdk.get_context(
    "What certified data set is used to make decisions on providing credit for customers?"
)
```

**Input Parameters**
- `question` (string): The natural language query
- `signature` (optional dict): The configuration controlling which objects and their fields

**Returns**
- JSON-formatted response of relevant catalog objects

## Shape the SDK to your needs

The SDK's `alation-context` tool supports customizing response content using signatures. This powerful feature allows you to specify which fields to include and how to filter the catalog results. For instance:

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

For more information about signatures, refer to [Using Signatures](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/signature.md).

## Guides and Example Agents

### General
- [Planning an Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/planning.md) - Practical considerations for getting the most out of your agents and the Alation Data Catalog.
- [Using Signatures](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/signature.md) - How to customize your agent with concrete examples.
- [Supported Object Types and Fields](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/supported.md) - See what's available.


### Model Context Protocol (MCP)

Enable agentic experiences with the Alation Data Catalog.

- [MCP Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/) - Getting the Alation MCP server up and running.
- [Testing with MCP Inspector](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/testing_with_mcp_inspector.md) - Steps for debugging and verification.
- [Claude Desktop Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/claude_desktop.md) - Leverage the Alation MCP server within Claude Desktop.
- [LibreChat Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/librechat.md) - Create assistants and agents alike.

### LangChain

Harness the SDK to build complex agents and workflows.
- [LangChain Integration](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/) - How to integrate the SDK into your LangChain agents.
- [Basic Usage Example](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/examples/basic_usage/) - A simple example.
- [Multi Agent Example](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/examples/multi_agent_return_eligibility/) - A multi agent workflow with several SDK integration points.

## Integrating with other toolkits

The number of published agent frameworks + toolkits appear to be increasing everyday. If you don't happen to see the framework or toolkit you're using here, it's still possible to adapt `alation-ai-agent-sdk` to your needs. It may as simple as writing a wrapping function where a decorator is applied.

While we want to reach as many developers as possible and make it as convenient as possible, we anticipate a long tail distribution of toolkits and won't be able to write adapters for every case.