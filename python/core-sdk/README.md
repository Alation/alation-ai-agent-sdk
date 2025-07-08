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

## Using the UpdateCatalogAssetMetadata Tool

The `UpdateCatalogAssetMetadata` tool allows you to update metadata for one or more Alation catalog assets using custom field values.

### Example

```python
from alation_ai_agent_sdk import AlationAIAgentSDK, ServiceAccountAuthParams

sdk = AlationAIAgentSDK(
    base_url="https://your-alation-instance.com",
    auth_method="service_account",
    auth_params=ServiceAccountAuthParams(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
)

custom_field_values = [
    {
        "oid": "123",
        "otype": "table",
        "field_id": 8,
        "value": "Updated value"
    },
    # ... more objects ...
]

result = sdk.update_catalog_asset_metadata(custom_field_values)
print(result)
```

## Check Job Status Tool

The `check_job_status` tool allows you to check the status of a bulk metadata job in Alation by job ID.

### Example Usage

```python
from alation_ai_agent_sdk import AlationAIAgentSDK

sdk = AlationAIAgentSDK(
    base_url="https://your-alation-instance.com",
    auth_method="service_account",
    auth_params=("your-client-id", "your-client-secret")
)

job_status = sdk.check_job_status(123)
print(job_status)
```

- **Parameters:**
  - `job_id` (int): The integer job identifier returned by a previous bulk operation.
- **Returns:**
  - The job status and details as a JSON object.
