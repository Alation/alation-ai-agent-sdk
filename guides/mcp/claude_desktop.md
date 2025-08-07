# Claude Desktop Integration - Alation MCP Server

This guide explains how to set up and use the Alation Model Context Protocol (MCP) server with Claude Desktop, allowing you to access Alation metadata and catalog information directly within your Claude conversations.

## Prerequisites

- [Claude Desktop](https://claude.ai/download) application installed (macOS or Windows)
- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).

## Quick start

### Step 1: Configure Claude Desktop

1. Open Claude Desktop and click on the Claude menu in the top menu bar
2. Select "Settings..."
3. Click on "Developer" in the left navigation
4. Click on "Edit Config" to open the configuration file

This will create or open the configuration file at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Method 1: Using `uvx`
> This method requires minimal setup, uvx downloads and installs the package in an isolated environment; Ensure uvx is installed in your environment

Add the following configuration to your `claude_desktop_config.json`. See [here](https://modelcontextprotocol.io/quickstart/user) for more details.

If you cannot obtain service account credentials (admin only), see the [User Account Authentication Guide](../authentication.md#user-account-authentication) for instructions.
```json
{
  "mcpServers": {
    "alation": {
      "command": "uvx",
      "args": [
        "--from", "alation-ai-agent-mcp", "start-alation-mcp-server"
      ],
      "env": {
        "ALATION_BASE_URL": "https://your-alation-instance.com",
        "ALATION_AUTH_METHOD": "service_account", // recommended

        // For service account authentication
        "ALATION_CLIENT_ID": "your-client-id",
        "ALATION_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

### Method 2: Using `pip`
1. Install the package: ```pip install alation-ai-agent-mcp``

2. After installation, you can use the start-alation-mcp-server command. Find the installation paths.
```
which start-alation-mcp-server  # On macOS/Linux
where start-alation-mcp-server  # On Windows
```
3. Add the following configuration to your `claude_desktop_config.json`.
```json
{
  "mcpServers": {
    "alation": {
      "command": "/full/path/to/start-alation-mcp-server",
      "env": {
        "ALATION_BASE_URL": "https://your-alation-instance.com",
        "ALATION_AUTH_METHOD": "service_account", // recommended

        // For service account authentication
        "ALATION_CLIENT_ID": "your-client-id",
        "ALATION_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

If you cannot obtain service account credentials (admin only), see the [User Account Authentication Guide](../authentication.md#user-account-authentication) for instructions.

### Method 3: Using Docker
> This assumes you've already locally built a docker image following the instructions from [this guide](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-mcp/README.md#debugging-the-server)
```json
{
  "mcpServers": {
    "alation-context-tool": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "ALATION_BASE_URL=https://your-alation-instance.com",
        "-e", "ALATION_AUTH_METHOD=service_account", // recommended
        // For service account authentication
        "-e", "ALATION_CLIENT_ID=your-client-id",
        "-e", "ALATION_CLIENT_SECRET=your-client-secret",
        "alation-mcp-server:latest"
      ]
    }
  }
}
```
If you cannot obtain service account credentials (admin only), see the [User Account Authentication Guide](../authentication.md#user-account-authentication) for instructions.

### Step 2: Save and Restart Claude Desktop

1. Save the configuration file
2. Completely close Claude Desktop
3. Relaunch the application

## Verifying the Connection

After restarting Claude Desktop, you should see a hammer icon (🔨) in the bottom right corner of the input box. This indicates MCP tools are available. Clicking on the hammer icon will display the list of available tools.

If you don't see this icon, check Claude Desktop logs for errors and verify your configuration.

## Using the Alation Tools in Claude

You can now ask Claude questions about your Alation catalog. Examples:

- "What are the commonly joined tables with customer_profile?"
- "Find recent documentation about our data warehouse"
- "Can you explain the difference between loan type and loan term?"
- "What certified data set is used to make decisions on providing credit for customers?"
- "Show me financial reporting datasets and related queries"
- "Retrieve data product with ID finance:loan_performance_analytics"
- "Search for data products related to customer analytics dashboards"

When needed, Claude will use the Alation MCP tools to retrieve contextual information or data products and will request your permission before executing tool calls.

## Using Signatures with Claude Desktop

The Alation AI Agent SDK supports customizing data retrieval through signatures. For detailed documentation on signature format and capabilities, see <a href="https://developer.alation.com/dev/docs/customize-the-aggregated-context-api-calls-with-a-signature" target="blank"> Using Signatures </a>.

### Example 1: Simple Usage with Claude

When asking Claude questions about your data catalog, you can provide a custom signature in your prompt:

```
Please use this signature when searching:

{
  "table": {
    "fields_required": ["name", "description", "columns"],
    "search_filters": {
      "flags": ["Endorsement"]
    },
    "child_objects": {
      "columns": {
        "fields": ["name", "data_type", "sample_values"]
      }
    }
  }
}

What tables do we have on claims? Fetch from alation.
```

This way, Claude will include this signature when making calls to the Alation context tool, ensuring you receive precisely the information you need, focused on trusted data sources with complete column details.

### Example 2: Using a Default Signature for All Queries

If you want Claude to always use a specific signature for all Alation-related queries in your conversation, you can specify this at the beginning:

For all Alation queries in this conversation, always use the following signature:
```json
{
  "table": {
    "fields_required": ["name", "description", "url"],
    "fields_optional": ["common_joins", "common_filters", "columns"],
    "search_filters": {
      "domain_ids": [42]  // Finance domain
    },
    "child_objects": {
      "columns": {
        "fields": ["name", "data_type", "description"]
      }
    }
  },
  "documentation": {
    "fields_required": ["title", "content", "url"],
    "search_filters": {
      "domain_ids": [42]  // Finance domain
    }
  }
}
```
Now, let's explore our financial data. What tables do we have related to revenue forecasting?

By specifying "always use" at the beginning, you establish a default signature that Claude will apply to all subsequent Alation queries in your conversation. This signature focuses on the finance domain (domain_id 42) and includes both table and documentation objects.

### Example 3: Providing Multiple Signatures for Different Query Types

For more complex scenarios, you can provide multiple signatures and let Claude select the most appropriate one based on your question:

I'm going to ask you questions about our data catalog. Please use the following signatures based on the type of question:

```json
For questions about table structure or data exploration:
{
  "table": {
    "fields_required": ["name", "description", "columns"],
    "child_objects": {
      "columns": {
        "fields": ["name", "data_type", "sample_values"]
      }
    }
  }
}

For questions about documentation or policies:
{
  "documentation": {
    "fields_required": ["title", "content", "url"]
  }
}
```

First question: What fields are available in our customer table?

In this example, you've provided two different signatures for different types of queries. Claude will analyze your question and apply the most appropriate signature based on the context.


###  Example 4: Bulk Retrieval - Get Endorsed Tables in a data source
```json
{
  "table": {
    "fields_required": ["name", "title", "description", "url"],
    "search_filters": {"flags": ["Endorsement"], "fields": {"ds": [1]}},
    "limit": 20
  }
}
```

Question: Use the above signature to fetch endorsed tables

Note: In bulk retrieval mode, the question is ignored. Results are based solely on the signature parameters. The question is shown only as an example of how to phrase such requests to ensure we call the right tool.

### Example 5: Data Product Creation

This example demonstrates a two-step workflow: first gathering catalog data, then creating a data product from that data.

First, ask:
```json
{
"table": {
        "fields_required": ["name", "description", "common_joins", "columns"],
        "search_filters": {
            "fields": {
                "domain_ids": 191  # This could be any other search criteria
            }
        },
        "child_objects": {
            "columns": {"fields": ["name", "data_type", "description"]}
        },
        "limit": 15
},
{
    "query": {
        "fields_required": ["title", "description", "content"],
        "search_filters": {
            "fields": {
                "domain_ids": 191  # This could be any other search criteria
            }
        },
        "limit": 5
    }
}
}
```
Please fetch content from alation using bulk retrieval tool based on above signature


Then, ask: Now use generate_data_product tool, use the above context and create a data product
