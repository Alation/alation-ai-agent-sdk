# Alation AI Agent SDK

The Alation AI Agent SDK is a Python library that enables AI agents to access and leverage metadata from the Alation Data Catalog.

## Overview

This SDK provides a simple, programmatic way for AI applications to:

- Retrieve contextual information from the Alation catalog using natural language questions
- Search for and retrieve data products by product ID or natural language queries
- Customize response formats using signature specifications

## Installation

```bash
pip install alation-ai-agent-sdk
```

## Prerequisites

To use the SDK, you'll need:

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).

## Quick Start

```python
from alation_ai_agent_sdk import AlationAIAgentSDK, UserAccountAuthParams, ServiceAccountAuthParams

# Initialize the SDK using user account authentication
sdk_user_account = AlationAIAgentSDK(
    base_url="https://your-alation-instance.com",
    auth_method="user_account",
    auth_params=UserAccountAuthParams(
        user_id=12345,
        refresh_token="your-refresh-token"
    )
)

# Initialize the SDK using service account authentication
sdk_service_account = AlationAIAgentSDK(
    base_url="https://your-alation-instance.com",
    auth_method="service_account",
    auth_params=ServiceAccountAuthParams(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
)

# Ask a question about your data
response = sdk_user_account.get_context(
    "What tables contain sales information?"
)
print(response)

# Use a signature to customize the response format
signature = {
    "table": {
        "fields_required": ["name", "title", "description"]
    }
}

response = sdk_user_account.get_context(
    "What are the customer tables?",
    signature
)
print(response)

# Retrieve a data product by ID
data_product_by_id = sdk_user_account.get_data_products(product_id="finance:loan_performance_analytics")
print(data_product_by_id)

# Search for data products using a natural language query
data_products_by_query = sdk_user_account.get_data_products(query="customer analytics dashboards")
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

For detailed documentation on signature format and capabilities, see [Using Signatures](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/signature.md).
### Getting Available Tools


```python
# Get all available tools
tools = sdk.get_tools()
```
