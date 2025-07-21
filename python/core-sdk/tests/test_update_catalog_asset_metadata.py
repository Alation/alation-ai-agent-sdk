from alation_ai_agent_sdk import AlationAIAgentSDK, ServiceAccountAuthParams


def test_update_catalog_asset_metadata(monkeypatch):
    sdk = AlationAIAgentSDK(
        base_url="https://mock-alation-instance.com",
        auth_method="service_account",
        auth_params=ServiceAccountAuthParams(
            client_id="mock-client-id", client_secret="mock-client-secret"
        ),
    )
    mock_response = {"job_id": 105}
    monkeypatch.setattr(sdk.api, "_with_valid_token", lambda: None)
    monkeypatch.setattr(
        sdk.api, "update_catalog_asset_metadata", lambda custom_field_values: mock_response
    )
    custom_field_values = [{"oid": "1", "otype": "table", "field_id": 8, "value": "Test Value"}]
    result = sdk.update_catalog_asset_metadata(custom_field_values)
    assert result == mock_response
