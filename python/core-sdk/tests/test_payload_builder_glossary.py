import pytest
from alation_ai_agent_sdk.api import CatalogAssetMetadataPayloadBuilder


def test_payload_builder_valid_glossary():
    payload = [
        {"oid": "1", "otype": "glossary_term", "field_id": 3, "value": "Some text"},
        {"oid": "2", "otype": "glossary_v3", "field_id": 4, "value": "<b>Rich text</b>"},
    ]
    result = CatalogAssetMetadataPayloadBuilder.build(payload)
    assert result == payload


def test_payload_builder_invalid_otype():
    payload = [{"oid": "1", "otype": "table", "field_id": 3, "value": "Some text"}]
    with pytest.raises(ValueError, match="Invalid otype"):
        CatalogAssetMetadataPayloadBuilder.build(payload)


def test_payload_builder_invalid_field_id():
    payload = [{"oid": "1", "otype": "glossary_term", "field_id": 8, "value": "Some text"}]
    with pytest.raises(ValueError, match="Invalid field_id"):
        CatalogAssetMetadataPayloadBuilder.build(payload)


def test_payload_builder_invalid_value_type():
    payload = [{"oid": "1", "otype": "glossary_term", "field_id": 3, "value": 123}]
    with pytest.raises(ValueError, match="field_id 3 \(TEXT\) requires a string value"):
        CatalogAssetMetadataPayloadBuilder.build(payload)
    payload2 = [{"oid": "1", "otype": "glossary_v3", "field_id": 4, "value": 123}]
    with pytest.raises(ValueError, match="field_id 4 \(RICH_TEXT\) requires a string value"):
        CatalogAssetMetadataPayloadBuilder.build(payload2)
