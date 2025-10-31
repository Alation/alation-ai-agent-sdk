# get_custom_fields_definitions

A retrieval tool that fetches field definitions from the Alation instance.

**Functionality**

This tools retrieves the custom  and built-in fields defined in Alation.
Note that this tool requires Catalog Admin or Server Admin permissions in order to retrieve any custom fields.

**Input Parameters**

No parameters required

**Returns**

- Admin users: JSON-formatted response with all custom fields plus built-in fields
- Non-admin users: Built-in fields only (title, description, steward) with informational message
