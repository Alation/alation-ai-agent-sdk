# get_custom_fields_definitions

A retrieval tool that fetches all custom field definitions from the Alation instance.

**Functionality**

- Retrieves all custom field definitions created by the organization
- Provides metadata about field types, allowed values, and object compatibility
- Returns built-in fields for non-admin users with appropriate messaging
- Includes usage guidance for implementing custom fields in applications

**Input Parameters**

No parameters required

**Returns**

- Admin users: JSON-formatted response with all custom fields plus built-in fields
- Non-admin users: Built-in fields only (title, description, steward) with informational message
