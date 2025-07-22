import requests
from unittest.mock import MagicMock
from alation_ai_agent_sdk import AlationAIAgentSDK, ServiceAccountAuthParams

# Global network call mocks for all tests
import pytest


@pytest.fixture(autouse=True)
def global_network_mocks(monkeypatch):
    # Mock requests.post for token generation
    def mock_post(url, *args, **kwargs):
        if "oauth/v2/token" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "access_token": "mock-jwt-access-token",
                "expires_in": 3600,
                "token_type": "Bearer",
            }
            return response
        return MagicMock(status_code=200, json=MagicMock(return_value={}))

    monkeypatch.setattr(requests, "post", mock_post)

    # Mock requests.get for license and version
    def mock_get(url, *args, **kwargs):
        if "/api/v1/license" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"is_cloud": True}
            return response
        if "/full_version" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"ALATION_RELEASE_NAME": "2025.1.2"}
            return response
        return MagicMock(status_code=200, json=MagicMock(return_value={}))

    monkeypatch.setattr(requests, "get", mock_get)


from alation_ai_agent_sdk.api import CatalogAssetMetadataPayloadItem


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
    custom_field_values: list[CatalogAssetMetadataPayloadItem] = [
        {"oid": "1", "otype": "glossary_term", "field_id": 3, "value": "Test Value"}
    ]
    result = sdk.update_catalog_asset_metadata(custom_field_values)
    assert result == mock_response
