# Supported Object Types and Fields

The `alation-context` tool currently supports the following object types and fields:

| Object Type | Fields |
-------------|--------|
| **Schema** | name, title, description, url |
| **Table** | name, title, description, url, common_joins*, common_filters*, columns* |
| **Column** | name, title, data_type, url, description*, sample_values* |
| **Documentation** (Includes Document, Article, Glossary, and Document Folder) | title, content, url |
| **Query** | title, description, content, url |

### Child Object Relationships

| Child Object | Parent Object | Fields |
|--------------|---------------|--------|
| **columns** | table | name, title, data_type, url*, description*, sample_values* |


## About Optional Fields
Fields marked with an asterisk (*) are optional fields that have special behavior only in the default scenario (when no signature is provided):

- Without a signature: These optional fields are automatically included when Alation's internal LLM determines they are relevant to your question
- With a signature: Optional fields are treated like any other field. You must explicitly specify them in your signature if you want them included:
  - Add to fields_required to always include them 
  - Add to fields_optional for dynamic inclusion