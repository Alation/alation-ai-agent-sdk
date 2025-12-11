# Langchain Integration

This package integrates the Alation AI Agent SDK with the Langchain framework, allowing Langchain agents to leverage metadata from the Alation Data Catalog.

## Overview

The Langchain integration enables:

- Using Alation's context tool within Langchain agent workflows
- Accessing Alation metadata through Langchain's structured tools interface
- Building sophisticated AI agents that can reason about your data catalog

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

## Prerequisites

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).
- If you cannot obtain service account credentials (admin only), see the [User Account Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md#user-account-authentication) for instructions.
## Installation

```bash
pip install alation-ai-agent-langchain
```

## Quick Start

```python
import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


from alation_ai_agent_sdk import AlationAIAgentSDK, ServiceAccountAuthParams
from alation_ai_agent_langchain import get_langchain_tools

# Initialize Alation SDK using service account authentication (recommended)

sdk = AlationAIAgentSDK(
    base_url=os.getenv("ALATION_BASE_URL"),
    auth_method="service_account",
    auth_params=ServiceAccountAuthParams(
        client_id=os.getenv("ALATION_CLIENT_ID"),
        client_secret=os.getenv("ALATION_CLIENT_SECRET")
    )
)

# Get Langchain tools
tools = get_langchain_tools(sdk)

# Define agent prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant using Alation's metadata catalog."),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Initialize LLM and create agent
llm = ChatOpenAI(model="gpt-4o", temperature=0)
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

# Create agent executor
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# Run the agent
response = executor.invoke({
  "input": "What tables contain customer data?"}
)
print(response)

```

## Using Signatures with Langchain

You can pass Alation signatures through the Langchain agent:

```python
# Define a signature to customize the response
tables_only_signature = {
  "table": {
    "fields_required": ["name", "title", "description", "url"]
  }
}

# Pass the signature with the input
response = executor.invoke({
    "input": "What tables contain sales data?",
    "signature": tables_only_signature,
})
print(response)
```


See the [examples directory](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/examples/) for a complete example of a return eligibility agent built with Langchain and Alation.