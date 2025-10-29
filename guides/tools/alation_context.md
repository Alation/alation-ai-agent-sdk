# alation_context

A retrieval tool that pulls contextual information from the Alation catalog based on natural language queries.

**Functionality**

- Accepts user questions in natural language
- Performs query rewrites to optimize search results
- Returns relevant catalog data in JSON format
- Can return multiple object types in a single response

**Usage**

``` {.sourceCode .python}
response = alation_ai_sdk.get_context(
    "What certified data set is used to make decisions on providing credit for customers?"
)
```

**Input Parameters**

- ` question ` (string): The natural language query
- ` signature ` (optional dict): The configuration controlling which objects and their fields

**Returns**

- JSON-formatted response of relevant catalog objects
