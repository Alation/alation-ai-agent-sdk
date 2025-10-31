# get_data_products

A retrieval tool that pulls data products from the Alation catalog based on product ID or natural language queries.

**Functionality**

Fetches data products if they match the provided parameters.
This tool can return multiple data products if they all match.
`product_id` will take precedence over `query` if both are provided. 

**Usage**

``` {.sourceCode .python}
response = alation_ai_sdk.get_data_products(
    "12345"  # Example product ID
)

response = alation_ai_sdk.get_data_products(
    "Show me all data products related to sales"
)
```

**Input Parameters**

- ` product_id ` (string, optional): The ID of the product for direct lookup
- ` query ` (string, optional): A natural language query to discover data products

**Returns**

- JSON-formatted response of relevant data products
