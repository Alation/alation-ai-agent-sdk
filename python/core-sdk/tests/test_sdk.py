import pytest
import requests

from alation_ai_agent_sdk import AlationAIAgentSDK


@pytest.fixture
def mock_requests_post(monkeypatch):
    """Fixture to mock requests"""

    def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {"api_access_token": "mock-token", "status": "success"}

        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)


@pytest.mark.parametrize(
    "base_url, user_id, refresh_token",
    [
        (None, 12345, "token"),  # Missing base_url
        ("", 12345, "token"),  # Empty base_url
        ("https://valid.url", None, "token"),  # Missing user_id
        ("https://valid.url", "not-an-integer", "token"),  # Invalid user_id
        ("https://valid.url", 12345, None),  # Missing refresh_token
        ("https://valid.url", 12345, ""),  # Empty refresh_token
    ],
)
def test_sdk_invalid_initialization(base_url, user_id, refresh_token, mock_requests_post):
    with pytest.raises(ValueError):
        AlationAIAgentSDK(
            base_url=base_url,
            user_id=user_id,
            refresh_token=refresh_token,
        )
