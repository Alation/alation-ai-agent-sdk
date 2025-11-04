# alation_context

A retrieval tool that pulls contextual information from the Alation catalog based on natural language queries.

**Functionality**

This tool takes in a natural language question, which will be used to find relevant catalog objects.
Examples of objects include: Schema, Table, Column, Query, Glossary, Document, Article, Term, BI Folder, BI Report, and BI Field.

See https://developer.alation.com/dev/reference/getaggregatedcontext for more details.

**Usage**

``` {.sourceCode .python}
response = alation_ai_sdk.get_context(
    "What certified data set is used to make decisions on providing credit for customers?"
)
```

**Input Parameters**

- ` question ` (string): The natural language query
- ` signature ` (optional dict): The configuration controlling which objects and their fields should be returned. See https://developer.alation.com/dev/reference/getaggregatedcontext#overview for more details on what can be passed.
- ` chat_id ` (optional, uuid): An existing chat to use. If not provided, a new chat will be created. 

**Returns**

- JSON-formatted response of relevant catalog objects

## Shape the SDK to your needs

The SDK's `alation-context` tool support customizing response content using signatures. This powerful feature allows you to specify which fields to include and how to filter the catalog results. For instance:

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
