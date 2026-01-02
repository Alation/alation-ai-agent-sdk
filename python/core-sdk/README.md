# Alation AI Agent SDK

The Alation AI Agent SDK is a Python library that enables AI agents to access and leverage metadata from the Alation Data Catalog.

## Overview

This SDK provides a simple, programmatic way for AI applications to:

- Retrieve contextual information from the Alation catalog using natural language questions
- Search for and retrieve data products by product ID or natural language queries
- Customize response formats using signature specifications

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

## Installation

```bash
pip install alation-ai-agent-sdk
```

## Prerequisites

To use the SDK, you'll need:

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).


## Quick Start

```python

from alation_ai_agent_sdk import AlationAIAgentSDK, ServiceAccountAuthParams

# Initialize the SDK using service account authentication (recommended)

sdk = AlationAIAgentSDK(
    base_url="https://your-alation-instance.com",
    auth_method="service_account",
    auth_params=ServiceAccountAuthParams(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
)

# Ask a question about your data
response = sdk.catalog_context_search_agent(
    "What tables contain sales information?"
)
print(response)

# Use a signature to customize the response format
signature = {
    "table": {
        "fields_required": ["name", "title", "description"]
    }
}

response = sdk.catalog_context_search_agent(
    "What are the customer tables?",
    signature
)
print(response)

# Retrieve a data product by ID
data_product_by_id = sdk.get_data_products(product_id="finance:loan_performance_analytics")
print(data_product_by_id)

# Search for data products using a natural language query
data_products_by_query = sdk.get_data_products(query="customer analytics dashboards")
print(data_products_by_query)
```


## Core Features

### Response Customization with Signatures

You can customize the data returned by the Alation context tool using signatures:

```python
# Only include specific fields for tables
table_signature = {
    "table": {
        "fields_required": ["name", "description", "url"]
    }
}

response = sdk.get_context(
    "What are our fact tables?",
    table_signature
)
```

For detailed documentation on signature format and capabilities, see <a href="https://developer.alation.com/dev/docs/customize-the-aggregated-context-api-calls-with-a-signature" target="blank"> Using Signatures </a>.
### Getting Available Tools


```python
# Get all available tools
tools = sdk.get_tools()
```
