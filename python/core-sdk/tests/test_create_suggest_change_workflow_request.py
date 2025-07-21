import pytest
from alation_ai_agent_sdk import AlationAIAgentSDK, ServiceAccountAuthParams
from alation_ai_agent_sdk.api import ChangeRequestCreateWorkflowExecutionPayload


def test_create_suggest_change_workflow_request(monkeypatch):
    sdk = AlationAIAgentSDK(
        base_url="https://mock-alation-instance.com",
        auth_method="service_account",
        auth_params=ServiceAccountAuthParams(client_id="dummy", client_secret="dummy"),
    )
    monkeypatch.setattr(
        sdk.api,
        "create_suggest_change_workflow_request",
        lambda payload: {"workflow_execution_id": 42, "status": "created"},
    )
    # Example payload for updating column (attribute) description (field_id=4)
    payload: ChangeRequestCreateWorkflowExecutionPayload = {
        "context": {"otype": "attribute", "field_id": 4, "oid": 1234},
        "input": {"change": {"proposed": "this is the new description"}},
    }
    result = sdk.create_suggest_change_workflow_request(payload)
    assert result["workflow_execution_id"] == 42
    assert result["status"] == "created"
