# update_catalog_asset_metadata

Updates metadata for Alation catalog assets by modifying existing objects.

**Functionality**

This tool can be used to update a single or multiple existing objects.
If multiple objects are provided, a bulk operation will be used.

The following object types are supported:
- 'glossary_term': Individual glossary terms (corresponds to document objects)
- 'glossary_v3': Glossary collections (corresponds to doc-folder objects, i.e., Document Hubs)

The following fields are supported: 
- field_id 3: Title (plain text)
- field_id 4: Description (supports rich text/HTML formatting)

**Input Parameters**

- ` custom_field_values ` (list): List of objects, each containing:
    - ` oid ` (string): Asset's unique identifier  
    - ` otype ` (string): Asset type - 'glossary_term' or 'glossary_v3'
    - ` field_id ` (int): Field to update - 3 for title, 4 for description
    - ` value ` (string): New value to set

Example usage:
- Single asset:
```json
[{"oid": "123", "otype": "glossary_term", "field_id": 3, "value": "New Title"}]
```
- Multiple assets:
```json
    [{"oid": 219, "otype": "glossary_v3", "field_id": 4, "value": "Sample Description"},
    {"oid": 220, "otype": "glossary_term", "field_id": 3, "value": "Another Title"}]
```

**Returns**
- Success:
    - Updates processed asynchronously
```json
{"job_id": <int>}    
```

- Error:
```json
{"title": "Invalid Payload", "errors": [...]}
```
