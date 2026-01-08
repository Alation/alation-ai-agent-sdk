import pytest
from unittest.mock import MagicMock, patch
from alation_ai_agent_sdk import AlationAPI, ServiceAccountAuthParams
import requests


# Global network call mocks for all tests
@pytest.fixture(autouse=True)
def global_network_mocks(monkeypatch):
    # Mock requests.post for token generation
    def mock_post(url, *args, **kwargs):
        if "createAPIAccessToken" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "api_access_token": MOCK_ACCESS_TOKEN,
                "status": "success",
            }
            response.raise_for_status.return_value = None
            return response
        elif "oauth/v2/token" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "access_token": MOCK_ACCESS_TOKEN,
                "expires_in": 3600,
                "token_type": "Bearer",
            }
            response.raise_for_status.return_value = None
            return response
        return MagicMock(status_code=200, json=MagicMock(return_value={}))

    monkeypatch.setattr(requests, "post", mock_post)

    # Mock requests.get for license and version
    def mock_get(url, *args, **kwargs):
        if "/api/v1/license" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"is_cloud": True}
            response.raise_for_status.return_value = None
            return response
        if "/full_version" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"ALATION_RELEASE_NAME": "2025.1.2"}
            response.raise_for_status.return_value = None
            return response
        response = MagicMock(status_code=200, json=MagicMock(return_value={}))
        response.raise_for_status.return_value = None
        return response

    monkeypatch.setattr(requests, "get", mock_get)


MOCK_BASE_URL = "https://mock-alation-instance.com"
MOCK_ACCESS_TOKEN = "mock-access-token"

# Mock responses based on data_products_spec.yaml
MOCK_PRODUCT_RESPONSE = {
    "id": "product_123",
    "name": "Mock Product",
    "description": "A mock data product for testing purposes",
    "status": "active",
}


@pytest.fixture
def alation_api():
    """Fixture to initialize AlationAPI instance."""
    api = AlationAPI(
        base_url=MOCK_BASE_URL,
        auth_method="service_account",
        auth_params=ServiceAccountAuthParams("mock-client-id", "mock-client-secret"),
    )
    api.access_token = MOCK_ACCESS_TOKEN
    return api


@pytest.fixture
def mock_token_methods(monkeypatch):
    """Mocks token validation and generation methods."""
    monkeypatch.setattr(
        "alation_ai_agent_sdk.api.AlationAPI._is_access_token_valid",
        lambda self: True,
    )
    monkeypatch.setattr(
        "alation_ai_agent_sdk.api.AlationAPI._generate_access_token_with_refresh_token",
        lambda self: None,
    )
    monkeypatch.setattr(
        "alation_ai_agent_sdk.api.AlationAPI._generate_jwt_token",
        lambda self: None,
    )


def test_get_data_products_by_id(alation_api, mock_token_methods):
    """Test get_data_products method with product_id using streaming endpoint."""
    mock_response = {
        "instructions": "The following is the complete specification for data product 'product_123'.",
        "results": [MOCK_PRODUCT_RESPONSE],
    }

    def mock_stream(*args, **kwargs):
        yield {"content": mock_response}

    with patch.object(
        alation_api, "get_data_product_spec_stream", side_effect=mock_stream
    ):
        response = alation_api.get_data_products(product_id="product_123")

    assert response["results"][0]["id"] == "product_123"


def test_get_data_products_by_id_not_found(alation_api, mock_token_methods):
    """Test get_data_products method with non-existent product_id."""

    def mock_stream(*args, **kwargs):
        # Empty generator - no events
        return iter([])

    with patch.object(
        alation_api, "get_data_product_spec_stream", side_effect=mock_stream
    ):
        response = alation_api.get_data_products(product_id="non_existent")

    assert response["instructions"] == "No data found"
    assert response["results"] == []


def test_get_data_products_query_multiple_results(alation_api, mock_token_methods):
    """Test get_data_products method when search returns multiple results."""
    mock_response = {
        "instructions": "Found 2 data products matching your query.",
        "results": [
            {"id": "product_123", "name": "Mock Product"},
            {"id": "product_456", "name": "Another Mock Product"},
        ],
    }

    def mock_stream(*args, **kwargs):
        yield {"content": mock_response}

    with patch.object(
        alation_api, "list_data_products_stream", side_effect=mock_stream
    ):
        response = alation_api.get_data_products(query="mock query")

    assert len(response["results"]) == 2
    assert response["results"][0]["id"] == "product_123"
    assert response["results"][1]["id"] == "product_456"


def test_get_data_products_query_single_result(alation_api, mock_token_methods):
    """Test get_data_products method when search returns exactly one result."""
    mock_response = {
        "instructions": "Found 1 data product matching your query.",
        "results": [{"id": "product_123", "name": "Mock Product"}],
    }

    def mock_stream(*args, **kwargs):
        yield {"content": mock_response}

    with patch.object(
        alation_api, "list_data_products_stream", side_effect=mock_stream
    ):
        response = alation_api.get_data_products(query="mock query")

    assert len(response["results"]) == 1
    assert response["results"][0]["id"] == "product_123"


def test_get_data_products_query_no_results(alation_api, mock_token_methods):
    """Test get_data_products method when search returns no results."""

    def mock_stream(*args, **kwargs):
        # Empty generator - no events
        return iter([])

    with patch.object(
        alation_api, "list_data_products_stream", side_effect=mock_stream
    ):
        response = alation_api.get_data_products(query="mock query")

    assert response["instructions"] == "No data found"
    assert response["results"] == []


def test_get_data_products_no_id_or_query(alation_api, mock_token_methods):
    """Test get_data_products method raises ValueError when neither ID nor query is passed."""
    with pytest.raises(
        ValueError,
        match="You must provide either a product_id or a query to search for data products.",
    ):
        alation_api.get_data_products()
