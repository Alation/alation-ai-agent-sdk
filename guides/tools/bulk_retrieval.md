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
