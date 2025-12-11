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
pip install uv

# Install the core SDK
uv pip install alation-ai-agent-sdk==1.0.0rc2

# Install LangChain integration
uv pip install alation-ai-agent-langchain==1.0.0rc2

# Install the MCP integration
uv pip install alation-ai-agent-mcp==1.0.0rc2

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

## New Major Version 1.x.x

#### Dec 10, 2025 Update
`1.0.0rc2` version of the Alation AI Agent SDK is now available.

It deprecates the Context Tool in favor of the more capable Catalog Context Search Agent. On the practical side, Catalog Context Search Agent shares the same contract so any migrations should be straightforward.

We've committed to keep the now deprecated Context Tool as part of the SDK for the next **three months for transition**. This means you should expect to see it **removed in Feb 2026**.

The main rationale for removing the Context Tool originates from having two tools which do very similar things. When both are exposed to an LLM, the model often picks the less capable one leading to worse outcomes. By reducing the number of tools that overlap conceptually, we're avoiding the wrong tool selection.

The Catalog Context Search Agent will do all the things the Context Tool did AND more like dynamically construct the `signature` parameter which was a major bottleneck when using the Context Tool.

Our local MCP server was changed for the same reason and no longer includes Context Tool, Analyze Catalog Question, Signature Create, or Bulk Retrieval by default. The Catalog Context Search Agent will invoke these internally as needed without requiring them in scope.

If you have prompts that expect any of those specific tools, you'll need to tell the MCP server which tools you wish to have enabled (overriding the default set). This can be done as a command line argument or as an environment variable.

Reminder: If you have a narrow use case, only enable the tools that are needed for that particular case.

```bash
# As command line arguments to the MCP server command
--enabled-tools=alation_context,analyze_catalog_question,bulk_retrieval,generate_data_product,get_custom_fields_definitions,get_data_dictionary_instructions,data_product,get_signature_creation_instructions,catalog_context_search_agent,query_flow_agent,sql_query_agent

# Or as an environment variable
export ALATION_ENABLED_TOOLS='alation_context,analyze_catalog_question,bulk_retrieval,generate_data_product,get_custom_fields_definitions,get_data_dictionary_instructions,data_product,get_signature_creation_instructions,catalog_context_search_agent,query_flow_agent,sql_query_agent'
```

#### Nov 4, 2025 Update
We're excited to announce the `1.0.0rc1` version of the Alation AI Agent SDK is available.

IMPORTANT: In a breaking change `user_account` is no longer supported as an authorization mode. We recommend you migrate to `service_account` or `bearer_token` modes.

The new major version comes with several notable changes that should make the transition worth it.
- Alation Agent Studio Integration
- Remote MCP Server
- Catalog Search Context Agent
- Streaming and Chat ID Support

### Alation Agent Studio Integration

The Alation Agent Studio gives you first class support for creating and leveraging the agents your business needs. Whether you're improving catalog curation or building data-centric query agents, the Agent Studio makes it easy to create agents, hone them, and deploy them across your enterprise. It includes a number of expert tools that are ready to be used or composed together as building blocks for more complex scenarios. And any precision agents you build are available within the SDK or MCP server as tools (See `custom_agent`).

### Remote MCP Server

We've heard from a number of customers that want the flexibility of MCP servers without the responsibility of having to install or upgrade the SDK. With our remote MCP server you don't have to do any of that. After a one time MCP focused authorization setup, it can be as simple as adding a remote MCP server to your favorite MCP client like: `https://<your_instance>/ai/mcp`

Note: MCP clients and platforms are rapidly evolving. Not all of them support authorization flows the same way nor path parameters etc. If you're running into blockers, please file an Issue so we can investigate and come up with a plan. We do not support dynamic client registration so please use an MCP client that allows you to pass in a `client_id` and `client_secret`.

#### Start Here

One issue the remote MCP server solves is listing tools dynamically. This dynamic portion is doing a lot of work for us. For instance, it can filter out tools the current user cannot use or it can list brand new tools the SDK doesn't even know about.

And since the tools are resolved lazily instead of statically, it means the API contracts for those tools can also be dynamic. This avoids client server version mismatches which could otherwise break static integrations.

We will continue to support the SDK and issue new versions regularly, but if you're after a less brittle more robust integration, you should consider integrating directly with the remote MCP server as a starting place.

### Catalog Search Context Agent

In the beginning of the Agent SDK we had only one tool: Alation Context. It offered a powerful way to dynamically select the right objects and their properties to best address a particular question. It's powerful `signature` parameter made it suitable for cases even without an user question (Bulk Retrieval). At the same time we saw a fair bit of friction with LLM generated `signature` parameters being invalid or just outright wrong. And a surprising amount of usage involved no `signature` at all which frequently resulted in poor results.

We've sought to address these issues by moving from a collection of these tools (`alation_context`, `bulk_retrieval`) into an agent that performs a series of checks and heuristics to dynamically create a `signature` when needed to take advantage of your custom fields. That is our new `catalog_search_context_agent`.

This should translate into fewer instructions you need to convince these tools to play nice with each other. And at the same time increase the accuracy of calls.

### Streaming and Chat ID Support

#### Streaming

All tools now support a streaming option. Primarily this benefits our local MCP server in http mode. If your MCP clients support streaming you should now see some of the internal processing of tools and agents to give you more transparency into what is happening under the hood.

By default the SDK has streaming disabled but it can be enabled if you have a use case for it. To enable it pass a `sdk_options=AgentSDKOptions(enable_streaming=True)` argument to the `AlationAIAgentSDK` constructor. When streaming you'll need to loop over the result or yield from it to correctly handle the underlying generator.

#### Chat ID

Most of our tools and agents accept the `chat_id` parameter when invoked. Including this will associate that tool call with any other prior calls referencing the same `chat_id`. Any `chat_id` compatible tool will include a `chat_id` in the response.

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




