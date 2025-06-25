# Using Signatures

## What are Signatures?

The signature feature allows you to customize the data returned from the Alation context tool (`alation-context`). This provides fine-grained control over the response format and content, enabling efficient and targeted retrieval from your Alation Data Catalog.

Signatures provide three main benefits:
- **Control which fields are returned** for each object type (tables, columns, etc.)
- **Filter results** to specific domains, tags etc.,
- **Configure child object relationships** (e.g., which column fields to include with tables)

## Signature Format

Signatures use a JSON format with this structure:

```json
{
  "{object_type}": {
    "fields_required": ["field1", "field2"], //List of fields
    "fields_optional": ["field3", "field4"], //List of fields
    "search_filters": {
      "domain_ids": [123, 456], //List of integer values
      "flags": ["Endorsement", "Deprecation", "Warning"],  // Only these three values are supported
      "fields": {
        "tag_ids": [789], //List of integer values
        "ds": [101], //List of integer values
        ...
      }
    },
    "limit": 10, // Maximum number of objects to return
    "child_objects": {
      "{child_type}": {
        "fields": ["field1", "field2"] //List of fields
      }
    }
  }
}
```

## Key Components

- **object_type**: The type of catalog object (table, column, schema, documentation, query)
- **fields_required**: Fields that will always be included in the response
- **fields_optional**: Fields that may be included if relevant to the query
- **search_filters**: Criteria to narrow down results
- **child_objects**: Configuration for related child objects

## Default Limits

- alation_context tool: 2 objects per object type
- bulk_retrieval tool: 50 objects per object type
- Maximum limit: 1000 objects per object type


## Examples

### Tables Only
```json
{
  "table": {
    "fields_required": ["name", "title", "description", "url"],
    "limit": 10
  }
}
```
This signature:

- Returns only table objects
- No `fields_optional` fields, so every response will only include name, title, description and url.
- Searches entire catalog (no filters)
- Returns maximum of 10 table objects

### Tables with dynamic field selection
```json
{
  "table": {
    "fields_required": ["name", "title", "description", "url"],
    "fields_optional": ["common_joins", "common_filters"]
  }
}
```
This signature:

- Returns only table objects
- Always includes name, title, description, and url in every response as they're required fields
- Intelligently includes common_joins and/or common_filters only when relevant to the user's question (e.g., if a user asks "What tables join with the sales table?", the response will include common_joins data)
- Searches entire catalog (no filters)

### Data Analyst Agent
```json
{
  "table": {
    "fields_required": ["name", "title", "description", "url", "common_joins", "common_filters", "columns"],
    "search_filters": {
      "flags": ["Endorsement"],
      "fields": {
        "tag_ids": [123] 
      }
    },
    "child_objects": {
      "columns": {
        "fields": ["name", "data_type", "description", "sample_values"]
      }
    }
  },
  "query": {
    "fields_required": ["title", "description", "content", "url"],
    "search_filters": {
       "fields": {
         "tag_ids": [123]
       }
    }
  },
  "documentation": {
    "fields_required": ["title", "content", "url"],
    "search_filters": {
      "fields": {
        "tag_ids": [123] 
      }
    }
  }
}
```

This signature:

- Returns `table`, `query`, and `documentation` objects relevant to the question.
- For `tables`:
  - Includes comprehensive information including `common_joins`, `common_filters` and `columns` details 
  - Filters for only trusted (Endorsed) tables with specific tag ID 123 
  - For each table, includes detailed column information with `sample_values`
- For `queries` and `documentation`:
  - Includes complete `content` to provide analysis context 
  - Filters to only include objects with `tag ID` 123
- Overall, this signature is optimized for analytical work by focusing on high-quality assets (Endorsed/tagged) with complete metadata

### Question Answering Agent

```json
{
  "schema": {
    "fields_required": ["name", "title", "description", "url"],
    "search_filters": {
      "domain_ids": [123]
    }
  },
  "table": {
    "fields_required": ["name", "title", "description", "url"],
    "fields_optional": ["common_joins", "common_filters", "columns"],
    "search_filters": {
      "domain_ids": [123]
    },
    "child_objects": {
      "columns": {
        "fields": ["name", "data_type", "description", "sample_values"]
      }
    }
  },
  "column": {
    "fields_required": ["name", "title", "data_type", "url"],
    "fields_optional": ["description", "sample_values"]
  },
  "documentation": {
    "fields_required": ["title", "content", "url"],
     "search_filters": {
      "domain_ids": [123]
    }
  },
  "query": {
    "fields_required": ["title", "description", "content", "url"],
    "search_filters": {
      "domain_ids": [123]
    }
  }
}
```
This signature:
- Designed for building a QA system focused on a specific business domain (domain ID 123), ensuring all responses remain relevant to that particular subject area
- Supports comprehensive QA by including all major object types (`schema`, `table`, `column`, `documentation`, and `query`)
- It's important to note that the Alation API will return only the relevant object types for each question, not all types in every response
- Uses optional fields for `tables` and `columns` to provide dynamic responses based on the question context

## Additional Notes
- Signatures are optional. If no signature is provided, by default the API searches all object types across the entire catalog.
- There is no dynamic selection for child object fields - all specified fields are always returned.
- A maximum of 50 child objects (ranked by popularity) are included in a single response to keep responses manageable for LLMs.
- For `common_joins` and `common_filters`, only the top 5 most frequent values are returned.