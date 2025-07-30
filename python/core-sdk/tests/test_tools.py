from alation_ai_agent_sdk.tools import csv_str_to_tool_list

def test_csv_str_to_tool_list():
    """Test conversion of CSV string to tool list."""
    csv_str = "tool1,tool2,tool3"
    expected_tools = ["tool1", "tool2", "tool3"]
    assert sorted(csv_str_to_tool_list(csv_str)) == sorted(expected_tools)

    # Test with extra spaces
    csv_str_with_spaces = " tool1 , tool2 , tool3 "
    assert sorted(csv_str_to_tool_list(csv_str_with_spaces)) == sorted(expected_tools)

    # Test with empty string
    assert csv_str_to_tool_list("") == []

    # Test with single tool
    assert csv_str_to_tool_list("single_tool") == ["single_tool"]

    # Test with duplicate tools
    csv_str_with_spaces_and_duplicate = " tool1 , tool2 , tool3, tool2"
    assert sorted(csv_str_to_tool_list(csv_str_with_spaces_and_duplicate)) == sorted(expected_tools)
