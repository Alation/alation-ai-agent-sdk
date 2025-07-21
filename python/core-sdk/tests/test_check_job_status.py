import pytest
from alation_ai_agent_sdk import AlationAIAgentSDK
from alation_ai_agent_sdk.api import AlationAPIError


class MockAPI:
    def check_job_status(self, job_id):
        if job_id == 123:
            return {"id": 123, "status": "completed", "result": "success"}
        raise AlationAPIError("Job not found", status_code=404)


class MockSDK:
    def __init__(self):
        self.check_job_status_tool = type(
            "Tool", (), {"run": lambda self, job_id: MockAPI().check_job_status(job_id)}
        )()

    def check_job_status(self, job_id):
        return self.check_job_status_tool.run(job_id)


def test_check_job_status_success():
    sdk = MockSDK()
    result = sdk.check_job_status(123)
    assert result["status"] == "completed"
    assert result["result"] == "success"


def test_check_job_status_not_found():
    sdk = MockSDK()
    with pytest.raises(AlationAPIError):
        sdk.check_job_status(999)
