import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_built_in_fields_structured() -> List[Dict[str, Any]]:
    """
    Returns built-in field definitions in the same structured format as custom fields.

    These are the core metadata fields available in all Alation instances:
    - Title (field_id 3): Object display name
    - Description (field_id 4): Rich text description
    - Steward (field_id 8): Responsible user or group

    Returns:
        List of built-in field objects with the same properties as custom fields
    """
    return [
        {
            "id": 3,
            "name_singular": "title",
            "field_type": "TEXT",
            "allowed_otypes": None,
            "tooltip_text": "Object title or display name. NOT allowed for BI objects.",
            "allow_multiple": False,
            "name_plural": ""
        },
        {
            "id": 4,
            "name_singular": "description",
            "field_type": "RICH_TEXT",
            "allowed_otypes": None,
            "tooltip_text": "Detailed description of the object. Supports HTML formatting.",
            "allow_multiple": False,
            "name_plural": ""
        },
        {
            "id": 8,
            "name_singular": "steward",
            "field_type": "OBJECT_SET",
            "allowed_otypes": ["user", "groupprofile"],
            "tooltip_text": "User or group responsible for this object. Use steward:user for users, steward:groupprofile for groups.",
            "allow_multiple": True,
            "name_plural": "stewards"
        }
    ]


def get_built_in_usage_guide() -> Dict[str, str]:
    """
    Returns usage guidance specifically for built-in fields.

    Provides comprehensive guidance on how to use built-in fields in various contexts
    including data dictionary CSV generation, API calls, and UI applications.

    Returns:
        Dictionary with usage guidance for built-in fields
    """
    return {
        "object_compatibility": "Built-in fields apply to most object types. Note: 'title' field is NOT allowed for BI objects (bi_server, bi_folder, bi_datasource, bi_datasource_column, bi_report, bi_report_column) as they are read-only from source systems.",
        "value_validation": "Title: plain text (max 255 chars). Description: rich text with HTML allowed. Steward: valid Alation username or group name. For multiple stewards, separate with semicolon (user1;user2).",
        "display_names": "Use 'name_singular' for field labels. For stewards with multiple values, use 'stewards' (name_plural).",
        "field_types": "TEXT = single line text, RICH_TEXT = formatted text with HTML, OBJECT_SET = references to users/groups. Built-in fields use these standard types.",
        "csv_headers": "For data dictionary CSV files: 3|title, 4|description, 8|steward:user (for users), 8|steward:groupprofile (for groups). This format is required for Alation to recognize which field to update.",
        "steward_formatting": "For steward field, specify the object type: 8|steward:user for individual users, 8|steward:groupprofile for group profiles. Multiple values separated by semicolon."
    }


def get_built_in_section() -> str:
    """
    Returns built-in fields formatted as instructional text for data dictionary generation.

    This is used in data dictionary instructions and maintains compatibility with
    existing data_dict.py formatting functions.

    Returns:
        Formatted string describing built-in fields for instructional purposes
    """
    return """
    ### Built-in Fields (Available to All Users)
    - **Title**: `3|title` (NOT allowed for BI objects)
    - **Description**: `4|description`
    - **Steward**: `8|steward:user (if its a user), 8|steward:groupprofile (if its a group profile)`
    """

def filter_field_properties(raw_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter custom fields to essential properties only."""
    filtered_fields = []
    selected_properties = [
        'id', 'name_singular', 'field_type', 'allowed_otypes',
        'options', 'tooltip_text', 'allow_multiple', 'name_plural'
    ]

    for field in raw_fields:
        filtered_field = {}
        for prop in selected_properties:
            filtered_field[prop] = field.get(prop)
        filtered_fields.append(filtered_field)

    return filtered_fields
