import pytest
from unittest.mock import patch, MagicMock
from alation_ai_agent_sdk import UserAccountAuthParams, AlationAPI, AlationAPIError

MOCK_BASE_URL = "https://mock-alation-instance.com"
MOCK_ACCESS_TOKEN = "mock-access-token"

# Mock responses based on data_products_spec.yaml
MOCK_PRODUCT_RESPONSE = {
    "id": "product_123",
    "name": "Mock Product",
    "description": "A mock data product for testing purposes",
    "status": "active",
}

MOCK_MARKETPLACE_RESPONSE = {
    "default_marketplace": "mock_marketplace",
}


@pytest.fixture
def mock_requests_get(monkeypatch):
    """Mocks requests.get for API calls."""
    mock_get_responses = {}

    def _add_mock_response(url_identifier, response_json=None, status_code=200):
        mock_get_responses[url_identifier] = {
            "response_json": response_json,
            "status_code": status_code,
        }

    def mock_get_router(*args, **kwargs):
        url = args[0]
        for identifier, mock_response in mock_get_responses.items():
            if identifier in url:
                print(f"Mocking response for URL: {url}")
                print(f"Response JSON: {mock_response['response_json']}")
                response_mock = MagicMock()
                response_mock.status_code = mock_response["status_code"]
                response_mock.json.return_value = (
                    mock_response["response_json"] if mock_response["response_json"] != [] else []
                )
                return response_mock
        raise ValueError(f"No mock response found for URL: {url}")

    monkeypatch.setattr("requests.get", mock_get_router)
    return _add_mock_response


@pytest.fixture
def mock_requests_post(monkeypatch):
    """Mocks requests.post for API calls."""
    mock_post_responses = {}

    def _add_mock_response(url_identifier, response_json=None, status_code=200):
        mock_post_responses[url_identifier] = {
            "response_json": response_json,
            "status_code": status_code,
        }

    def mock_post_router(*args, **kwargs):
        url = args[0]
        print(f"Intercepting POST request to URL: {url}")
        print(f"Request body: {kwargs.get('json', {})}")
        for identifier, mock_response in mock_post_responses.items():
            if identifier in url:
                print(f"Mocking response for URL: {url}")
                response_mock = MagicMock()
                response_mock.status_code = mock_response["status_code"]
                response_mock.json.return_value = mock_response["response_json"]
                return response_mock
        raise ValueError(f"No mock response found for URL: {url}")

    monkeypatch.setattr("requests.post", mock_post_router)
    return _add_mock_response


@pytest.fixture
def alation_api():
    """Fixture to initialize AlationAPI instance."""
    api = AlationAPI(
        base_url=MOCK_BASE_URL,
        auth_method="user_account",
        auth_params=UserAccountAuthParams(123, "mock-refresh-token"),
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


def test_get_data_products_by_id(alation_api, mock_requests_get, mock_token_methods):
    """Test get_data_products method with product_id."""
    mock_requests_get(
        "data-product/product_123",
        response_json=MOCK_PRODUCT_RESPONSE,
        status_code=200,
    )

    response = alation_api.get_data_products(product_id="product_123")

    assert len(response["results"]) == 1
    assert response["results"][0]["id"] == "product_123"
    assert (
        response["instructions"]
        == "The following is the complete specification for data product 'product_123'."
    )


def test_get_data_products_by_id_not_found(alation_api, mock_requests_get, mock_token_methods):
    """Test get_data_products method with non-existent product_id."""
    mock_requests_get(
        "data-product/non_existent",
        response_json=[],  # Ensure this returns an empty list
        status_code=200,
    )

    response = alation_api.get_data_products(product_id="non_existent")

    assert len(response["results"]) == 0
    assert response["instructions"] == "No data products found for the given product ID."


def test_get_data_products_query_multiple_results(
    alation_api, mock_requests_post, mock_requests_get, mock_token_methods
):
    """Test get_data_products method when search-internally returns multiple results."""
    mock_requests_get(
        "setting/marketplace",
        response_json=MOCK_MARKETPLACE_RESPONSE,
        status_code=200,
    )
    mock_requests_post(
        "search-internally/mock_marketplace",
        response_json=[
            {
                "product": {
                    "product_id": "product_123",
                    "spec_json": {
                        "product": {
                            "en": {
                                "name": "Mock Product",
                                "description": "Mock data product for testing purposes",
                            }
                        }
                    },
                }
            },
            {
                "product": {
                    "product_id": "product_456",
                    "spec_json": {
                        "product": {
                            "en": {
                                "name": "Another Mock Product",
                                "description": "Another mock data product for testing purposes",
                            }
                        }
                    },
                }
            },
        ],
        status_code=200,
    )

    response = alation_api.get_data_products(query="mock query")

    assert len(response["results"]) == 2
    assert response["results"][0]["id"] == "product_123"
    assert response["results"][1]["id"] == "product_456"
    assert response["instructions"] == (
        "Found 2 data products matching your query. "
        "The following contains summary information (name, id, description, url) for each product. "
        "To get complete specifications, call this tool again with a specific product_id."
    )


def test_get_data_products_query_single_result(
    alation_api, mock_requests_post, mock_requests_get, mock_token_methods
):
    """Test get_data_products method when search-internally returns exactly one result."""
    mock_requests_get(
        "setting/marketplace",
        response_json=MOCK_MARKETPLACE_RESPONSE,
        status_code=200,
    )
    mock_requests_post(
        "search-internally/mock_marketplace",
        response_json=[
            {
                "product": {
                    "product_id": "product_123",
                    "spec_json": {
                        "product": {
                            "en": {
                                "name": "Mock Product",
                                "description": "Mock data product for testing purposes",
                            }
                        }
                    },
                }
            }
        ],
        status_code=200,
    )

    response = alation_api.get_data_products(query="mock query")

    assert len(response["results"]) == 1
    assert response["results"][0]["id"] == "product_123"
    assert response["instructions"] == (
        "Found 1 data products matching your query. "
        "The following contains summary information (name, id, description, url) for each product. "
        "To get complete specifications, call this tool again with a specific product_id."
    )


def test_get_data_products_query_marketplace_not_found(
    alation_api, mock_requests_get, mock_token_methods
):
    """Test get_data_products method when marketplace ID is missing."""
    mock_requests_get(
        "setting/marketplace",
        response_json={},
        status_code=200,
    )

    with pytest.raises(AlationAPIError, match="Marketplace ID not found in response"):
        alation_api.get_data_products(query="mock query")


def test_get_data_products_query_no_results(
    alation_api, mock_requests_post, mock_requests_get, mock_token_methods
):
    """Test get_data_products method when search-internally returns no results."""
    mock_requests_get(
        "setting/marketplace",
        response_json=MOCK_MARKETPLACE_RESPONSE,
        status_code=200,
    )
    mock_requests_post(
        "search-internally/mock_marketplace",
        response_json=[],
        status_code=200,
    )

    response = alation_api.get_data_products(query="mock query")

    assert len(response["results"]) == 0
    assert response["instructions"] == "No data products found for the given query."


def test_get_data_products_no_id_or_query(alation_api, mock_token_methods):
    """Test get_data_products method raises ValueError when neither ID nor query is passed."""
    with pytest.raises(
        ValueError,
        match="You must provide either a product_id or a query to search for data products.",
    ):
        alation_api.get_data_products()
