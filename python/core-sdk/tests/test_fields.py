from alation_ai_agent_sdk.fields import (
    filter_field_properties,
    get_built_in_fields_structured,
    get_built_in_usage_guide,
    get_built_in_section,
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
            "another_unwanted": 12345,
        }
    ]

    filtered = filter_field_properties(raw_fields)

    assert len(filtered) == 1
    field = filtered[0]

    # Should have exactly 8 properties
    assert len(field) == 8

    # Should have required properties
    expected_props = [
        "id",
        "name_singular",
        "field_type",
        "allowed_otypes",
        "options",
        "tooltip_text",
        "allow_multiple",
        "name_plural",
    ]
    for prop in expected_props:
        assert prop in field

    # Should not have unwanted properties
    assert "unwanted_field" not in field
    assert "another_unwanted" not in field


def test_filter_field_properties_empty_list():
    """Test field filtering with empty list."""
    result = filter_field_properties([])
    assert result == []


def test_get_built_in_fields_structured():
    """Test built-in fields structure."""
    fields = get_built_in_fields_structured()

    assert isinstance(fields, list)
    assert len(fields) == 3

    # Check field IDs are present
    field_ids = [field["id"] for field in fields]
    assert 3 in field_ids  # title
    assert 4 in field_ids  # description
    assert 8 in field_ids  # steward


def test_get_built_in_usage_guide():
    """Test built-in usage guide."""
    guide = get_built_in_usage_guide()

    assert isinstance(guide, dict)
    assert "object_compatibility" in guide
    assert "value_validation" in guide
    assert "csv_headers" in guide


def test_get_built_in_section():
    """Test built-in section formatting."""
    section = get_built_in_section()

    assert isinstance(section, str)
    assert "3|title" in section
    assert "4|description" in section
    assert "8|steward" in section
