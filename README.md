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

The library needs to be configured with your Alation instance credentials. Depending on your authentication mode, you can use either `UserAccountAuthParams` or `ServiceAccountAuthParams`.


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

### alation_context

<details>
<summary>
A retrieval tool that pulls contextual information from the Alation catalog based on natural language queries.
</summary>

<br />

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
</details>

### get_data_products
<details>
<summary>
A retrieval tool that pulls data products from the Alation catalog based on product ID or natural language queries.
</summary>

<br />

**Functionality**
- Accepts product IDs for direct lookup
- Accepts user queries in natural language for discovery
- Returns relevant data products in JSON format
- Can return single or multiple results

**Usage**
```python
response = alation_ai_sdk.get_data_products(
    "12345"  # Example product ID
)

response = alation_ai_sdk.get_data_products(
    "Show me all data products related to sales"
)
```

**Input Parameters**
- `product_id` (string, optional): The ID of the product for direct lookup
- `query` (string, optional): A natural language query to discover data products

**Returns**
- JSON-formatted response of relevant data products

</details>

### bulk_retrieval
<details>
<summary>
A retrieval tool that pulls a set of objects from the Alation catalog based on a signature.
</summary>

<br />

**Functionality**
- Retrieve catalog objects without conversational queries.
- Useful for having an LLM decide which items to use from a larger set.
- Accepts a signature defining which objects and the fields required.
- Returns relevant catalog data in JSON format
- Can return multiple object types in a single response

**Usage**
```python
# Get tables from a specific datasource
bulk_signature = {
    "table": {
        "fields_required": ["name", "description", "columns"],
        "search_filters": {
            "fields": {"ds": [123]}  # Specific datasource
        },
        "limit": 100,
        "child_objects": {
            "columns": {
                "fields": ["name", "data_type", "description"]
            }
        }
    }
}

response = sdk.bulk_retrieval(signature=bulk_signature)
```

**Input Parameters**
- `signature` (dict): The configuration controlling which objects and their fields

**Returns**
- JSON-formatted response of relevant data products

</details>

### check_job_status

<details>
<summary>
A tool for checking the status of asynchronous jobs.
</summary>

<br />

**Functionality**
- Used to monitor progress and completion of async jobs.
- Accepts a job id
- Returns the job detail object including status

**Input Parameters**
- `job_id` (int): The identifier of the asychronous job.

**Returns**
- JSON-formatted response of the job details

</details>

### update_catalog_metadata

<details>
<summary>
A tool to updates metadata for Alation catalog assets by modifying existing objects.
</summary>

<br />

**Supported object types**
- `glossary_term`: Individual glossary terms (corresponds to document objects)
- `glossary_v3`: Glossary collections (corresponds to doc-folder objects, i.e., Document Hubs)

**Functionality**
- Creates an async job that updates one or more object field values.

**Input Parameters**
- A list of objects to be updated which include the `id`, `otype`, `field_id`, and the new `value`.

**Returns**
- validation error (dict) A dictionary containing a "error" value.
- on success (dict) A dictionary containing a "job_id" value.

</details>

### generate_data_product

<details>
<summary>
A tool that provides complete instructions and schema for creating Alation Data Products.
</summary>

<br />

**Functionality**
- Fetches the current Alation Data Product schema dynamically from your instance
- Includes detailed instructions for converting user input to valid YAML

**Input Parameters**
- No parameters required

**Returns**
- Complete instruction set with the latest schema from your Alation instance

</details>

### lineage

<details>
<summary>
A lineage retrieval tool to identify upstream or downstream objects relative to the starting object. Supports Column level lineage.
</summary>

<br />

**NOTE**: This BETA feature must be enabled on the Alation instance. Please contact Alation support to do this. Additionally, the lineage tool within the SDK must be explicitly enabled.

**Functionality**
- Access the object's upstream or downstream lineage.
- Graph is filterable by object type.
- Helpful for root cause and impact analysis
- Enables custom field value propagation

**Input Parameters**
- `root_node` (dict) The starting object. Must contain `id` and `otype`.
- `direction` (upsteam|downstream) The direction to resolve the lineage graph from.
- `limit` (optional int) Defaults to 1,000.
- `batch_size` (optional int) Defaults to 1,000.
- `max_depth` (optional int) The maximumn depth to transerve of the graph. Defaults to 10.
- `allowed_otypes` (optional string[]) Controls which types of nodes are allowed in the graph.
- `pagination` (optional dict) Contains information about the request including cursor identifier.
- `show_temporal_objects` (optional bool) Defaults to false.
- `design_time` (optional 1,2,3) 1 for design time objects. 2 for run time objects. 3 for both design and run time objects.
- `excluded_schema_ids` (optional int[]) Remove nodes if they belong to these schemas.
- `time_from` (optional timestamp w/o timezone) Controls the start point of a time period.
- `time_to` (optional timestamp w/o timezone) Controls the ending point of a time period.

**Returns**
- (dict) An object containing the lineage graph, the direction, and any pagination values.
</details>

### get_custom_fields_definitions
<details>
<summary>
A retrieval tool that fetches all custom field definitions from the Alation instance.
</summary>
<br />

**Functionality**

- Retrieves all custom field definitions created by the organization
- Provides metadata about field types, allowed values, and object compatibility
- Returns built-in fields for non-admin users with appropriate messaging
- Includes usage guidance for implementing custom fields in applications


**Input Parameters**

No parameters required

**Returns**

- Admin users: JSON-formatted response with all custom fields plus built-in fields
- Non-admin users: Built-in fields only (title, description, steward) with informational message
</details>


### get_data_dictionary_instructions
<details>
<summary>
A tool that generates comprehensive instructions for creating Alation Data Dictionary CSV files.
</summary>
<br />

**Functionality**

- Dynamically fetches current custom field definitions from your instance
- Provides complete CSV format specifications with required headers
- Includes object hierarchy grouping requirements and validation rules
- Generates field-specific examples and transformation guidelines
- Returns ready-to-use instructions for LLMs and developers


**Input Parameters**

No parameters required

**Returns**

Complete instruction set with custom fields and examples for generating data dictionary.

</details>


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
- [Data Quality: Check SQL Query](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/tools/data_quality_tool.md) - Indentifies data quality issues within a SQL query.
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
