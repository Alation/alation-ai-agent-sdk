import logging
from typing import Any, Dict, List

from alation_ai_agent_sdk.fields import get_built_in_section

logger = logging.getLogger(__name__)

def build_optimized_instructions(custom_fields: List[Dict[str, Any]]) -> str:
    """Build optimized instruction set with better organization and less redundancy."""

    # Build components
    quick_reference = build_quick_reference()
    hierarchy_rules = build_hierarchy_rules()
    csv_format = build_csv_format_section(custom_fields)
    process_steps = build_process_steps()
    examples = build_focused_examples(custom_fields)
    validation_reference = build_validation_reference(custom_fields)

    instructions = f"""# Alation Data Dictionary CSV Generation Instructions

## QUICK REFERENCE

{quick_reference}

## HIERARCHY GROUPING RULES

{hierarchy_rules}

## CSV FORMAT & HEADERS

{csv_format}

## PROCESS STEPS

{process_steps}

## EXAMPLES

{examples}

## VALIDATION REFERENCE

{validation_reference}

## CRITICAL REMINDERS

- **ZERO HALLUCINATION**: Only use information explicitly provided by the user
- **ONE CSV PER HIERARCHY**: Never separate objects from the same hierarchy
- **EMPTY CELLS OK**: Different object types may use different fields in same CSV
- **BI TITLE RESTRICTION**: Never use title field for BI objects (causes upload failure)

Remember: Transform only what the user provides. Do not enhance, assume, or add any information not explicitly given.
"""
    return instructions

def build_quick_reference() -> str:
    """Build a concise quick reference section."""
    return """
**TL;DR**: 
1. Group objects by hierarchy → Create one CSV per hierarchy
2. Use format: `al_datadict_item_properties,<field_headers>`
3. Each row: `oid=<id>;otype=<type>,<field_values>`

**File Count**: Number of hierarchies in your data = Number of CSV files needed
"""

def build_hierarchy_rules() -> str:
    """Build focused hierarchy rules without repetition."""
    return """
Objects must be grouped by hierarchy into separate CSV files:

| Hierarchy | Object Types | File Name |
|-----------|--------------|-----------|
| **RDBMS** | data, schema, table, attribute | `RDBMS_DataDictionary.csv` |
| **BI** | bi_server, bi_folder, bi_datasource, bi_datasource_column, bi_report, bi_report_column | `BI_DataDictionary.csv` |
| **Documentation** | glossary_v3, glossary_term | `Documentation_DataDictionary.csv` |

**Key Rule**: ALL objects from same hierarchy go in ONE CSV file together.

**Examples**:
- 5 tables + 50 columns → 1 RDBMS CSV (55 rows)
- 3 BI reports + 2 BI folders → 1 BI CSV (5 rows)  
- 10 tables + 2 BI reports → 2 CSV files (RDBMS + BI)
"""

def build_csv_format_section(custom_fields: List[Dict[str, Any]]) -> str:
    """Build concise CSV format section."""

    built_in_section = get_built_in_section()

    if not custom_fields:
        custom_section = """
### Custom Fields
No custom fields available (requires admin permissions).
"""
    else:
        custom_section = "\n### Custom Fields:\n"
        display_fields = custom_fields
        for field in display_fields:
            field_id = field.get('id')
            name = field.get('name_singular', 'Unknown')
            field_type = field.get('field_type', 'TEXT')

            if field_type == 'OBJECT_SET' and field.get('allowed_otypes'):
                # For OBJECT_SET fields with multiple allowed types, show examples for each type
                allowed_types = field.get('allowed_otypes')
                if len(allowed_types) > 1:
                    # Show separate examples for each object type
                    examples = []
                    for obj_type in allowed_types:
                        examples.append(f"`{field_id}|{name}:{obj_type}`")
                    header_format = " or ".join(examples)
                else:
                    # Single object type
                    header_format = f"`{field_id}|{name}:{allowed_types[0]}`"
            else:
                header_format = f"`{field_id}|{name}`"

            custom_section += f"- **{name}** ({field_type}): {header_format}\n"

    return f"""
### Required Structure
```
al_datadict_item_properties,<field_headers>
oid=<id>;otype=<type>,<field_values>
```

{built_in_section}
{custom_section}
"""

def build_process_steps() -> str:
    """Build streamlined process steps."""
    return """
1. **Analyze**: Identify object types → Determine hierarchies present
2. **Group**: Create one CSV per hierarchy (combine all objects from same hierarchy)
3. **Headers**: Add `al_datadict_item_properties` + field headers for data you have
4. **Populate**: One row per object with `oid=<id>;otype=<type>` + field values
5. **Validate**: Check picker values, date formats, steward names
"""

def build_focused_examples(custom_fields: List[Dict[str, Any]]) -> str:
    """Build focused examples showing key patterns."""

    base_examples = """
### RDBMS Example (Tables + Columns Together) 
Note: Columns are referred to as Attributes.
```csv
al_datadict_item_properties,3|title,4|description
oid=41;otype=table,Customer Master,Main customer information table
oid=719;otype=attribute,,Account balance amount in USD
```

### RDBMS Example (Table with Multiple Stewards)
```csv
al_datadict_item_properties,3|title,8|steward:user
oid=41;otype=table,Customer Master,"sally@alationmail.com;mark@alationmail.com"
```

### RDBMS Example with Multi Picker (Increase Productivity)
```csv
al_datadict_item_properties,10063|Increase Productivity
oid=41;otype=table,"[""Analyst/Data Scientist Productivity"", ""Decision Maker Confidence""]"
```

### BI Example (Multiple BI Types Together - No Title Field)
```csv
al_datadict_item_properties,4|description,8|steward:user
oid=5432;otype=bi_report,Monthly sales dashboard,user-name
oid=5433;otype=bi_datasource,CRM sales data,
oid=5434;otype=bi_report_column,Revenue column,
```
"""

    if custom_fields and len(custom_fields) > 0:
        # Use first custom field for example
        sample_field = custom_fields[0]
        field_id = sample_field.get('id')
        field_name = sample_field.get('name_singular')

        custom_example = f"""
### Mixed Updates Example (Built-in + Custom Fields)
```csv
al_datadict_item_properties,{field_id}|{field_name},4|description
oid=41;otype=table,Yes,Banking account details table
oid=719;otype=attribute,,Current account balance amount
```
"""
        return base_examples + custom_example

    return base_examples

def build_validation_reference(custom_fields: List[Dict[str, Any]]) -> str:
    """Build concise validation reference."""

    base_validation = """
### Built-in Field Rules
- **Title**: Plain text, max 255 chars, NOT for BI objects
- **Description**: Rich text with HTML allowed
- **Steward**: Valid Alation username or group name. For multiple, separate with a semicolon (e.g., `user1;user2`)
- **Dates**: YYYY-MM-DD format
"""

    if not custom_fields:
        return base_validation

    validation_summary = "\n### Custom Field Rules\n"
    # Rule for MULTI_PICKER
    validation_summary += (
        "- **MULTI_PICKER Fields**: For multiple values, use a string formatted like a Python list. "
        "Example: `\"[\"\"Value 1\"\", \"\"Value 2\"\"]\"`\n"
    )
    # Rule for OBJECT_SET
    validation_summary += (
        "- **OBJECT_SET Fields**: For multiple values, separate each value with a semicolon (`;`). "
        "Example: `object1;object2`\n"
    )

    date_fields = [f for f in custom_fields if f.get('field_type') == 'DATE']
    if date_fields:
        validation_summary += f"- **Date Fields**: {len(date_fields)} fields requiring YYYY-MM-DD format\n"

    validation_summary += "- **Other Fields**: Accept plain text or rich text\n"

    return base_validation + validation_summary
