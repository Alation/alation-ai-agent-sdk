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

*Note: Fields marked with * are optional fields.*