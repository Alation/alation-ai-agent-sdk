import pytest

from alation_ai_agent_sdk.data_dict import (
    filter_field_properties,
    build_optimized_instructions,
    build_process_steps,
    build_hierarchy_rules,
    build_quick_reference
)


def test_filter_field_properties():
    """Test the field filtering function."""
    raw_fields = [
        {
            "id": 10001,
            "name_singular": "Test Field",
            "field_type": "TEXT",
            "allowed_otypes": ["table"],
            "options": None,
            "tooltip_text": "Test tooltip",
            "allow_multiple": False,
            "name_plural": "Test Fields",
            "unwanted_field": "should_be_removed",
            "another_unwanted": 12345
        }
    ]

    filtered = filter_field_properties(raw_fields)

    assert len(filtered) == 1
    field = filtered[0]

    # Should have exactly 8 properties
    assert len(field) == 8

    # Should have required properties
    expected_props = ['id', 'name_singular', 'field_type', 'allowed_otypes',
                      'options', 'tooltip_text', 'allow_multiple', 'name_plural']
    for prop in expected_props:
        assert prop in field

    # Should not have unwanted properties
    assert "unwanted_field" not in field
    assert "another_unwanted" not in field


def test_filter_field_properties_empty_list():
    """Test field filtering with empty list."""
    result = filter_field_properties([])
    assert result == []


def test_build_quick_reference():
    """Test quick reference section generation."""
    result = build_quick_reference()
    assert isinstance(result, str)
    assert "al_datadict_item_properties" in result
    assert "oid=" in result
    assert "otype=" in result


def test_build_hierarchy_rules():
    """Test hierarchy rules section generation."""
    result = build_hierarchy_rules()
    assert isinstance(result, str)
    assert "RDBMS" in result
    assert "BI" in result
    assert "Documentation" in result


def test_build_optimized_instructions_with_custom_fields():
    """Test complete instruction generation with custom fields."""
    custom_fields = [
        {
            "id": 10001,
            "name_singular": "Test Field",
            "field_type": "TEXT",
            "allowed_otypes": None,
            "options": None,
            "tooltip_text": None,
            "allow_multiple": False,
            "name_plural": ""
        }
    ]

    instructions = build_optimized_instructions(custom_fields)

    # Verify all required sections
    required_sections = [
        "QUICK REFERENCE",
        "HIERARCHY GROUPING RULES",
        "CSV FORMAT & HEADERS",
        "PROCESS STEPS",
        "EXAMPLES",
        "VALIDATION REFERENCE",
        "CRITICAL REMINDERS"
    ]

    for section in required_sections:
        assert section in instructions

    # Verify custom field is included
    assert "Test Field" in instructions
    assert "10001" in instructions


def test_build_optimized_instructions_without_custom_fields():
    """Test complete instruction generation without custom fields."""
    instructions = build_optimized_instructions([])

    # Should still have all sections
    assert "QUICK REFERENCE" in instructions
    assert "CSV FORMAT & HEADERS" in instructions

    # Should mention built-in fields
    assert "Built-in Fields" in instructions
    assert "3|title" in instructions

    # Should indicate no custom fields
    assert "No custom fields available" in instructions