# bulk_retrieval

A retrieval tool that pulls a set of objects from the Alation catalog based on a signature.

**Functionality**

- Retrieve catalog objects without conversational queries.
- Useful for having an LLM decide which items to use from a larger set.
- Accepts a signature defining which objects and the fields required.
- Returns relevant catalog data in JSON format
- Can return multiple object types in a single response

**Usage**

``` {.sourceCode .python}
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

- ` signature ` (dict): The configuration controlling which objects and their fields
- ` chat_id ` (optional, uuid): An existing chat to use. If not provided, a new chat will be created. 

**Returns**

- JSON-formatted response of relevant data products

## Shape the SDK to your needs

The SDK's `bulk_retrieval` tool supports customizing response content using signatures. This powerful feature allows you to specify which fields to include and how to filter the catalog results. For instance:

```python
# Define a signature for searching only tables. Return joins and filters.
signature = {
    "table": {
        "fields_required": ["name", "title", "description", "common_joins", "common_filters"],
    }
}

# Use the signature with your query
response = sdk.bulk_retrieval_tool(
    signature=signature
)
```

For more information about signatures, refer to
<a href="https://developer.alation.com/dev/docs/customize-the-aggregated-context-api-calls-with-a-signature" target="blank"> Using Signatures </a>
