# catalog_context_search_agent

Catalog Context Search Agent for searching catalog objects with enhanced context.

**Functionality**

This agent understands the relationships in the Alation catalog and is able to perform contextual searching over it.
Invokers can provide a natural language query, which will then be used to search, and eventually output a data-enriched result.

**Input Parameters**

- ` message ` (required, str): Natural language description of what you're searching for
- ` chat_id ` (optional, uuid): An existing chat to use. If not provided, a new chat will be created. 

**Returns**

- Contextually-aware search results with enhanced metadata and relationships.
