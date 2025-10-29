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
