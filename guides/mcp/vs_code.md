# Adding MCP Server to VSCode

This guide explains how to add the MCP server to VSCode.

## Prerequisites

Ensure you are using VSCode version **April 2025 (version 1.100)** or newer.

## Steps

1. Navigate to the root of your repository.
2. Create a `.vscode` folder if it does not already exist.
3. Add a `mcp.json` file in the `.vscode` folder with the following content:

    ```json
    {
        "servers": {
            "alation-mcp-server": {
                "command": "uvx",
                "args": [
                    "--from", "alation-ai-agent-mcp", "start-mcp-server"
                ],
                "env": {
                    "ALATION_BASE_URL": "https://company.alationcloud.com",
                    "ALATION_AUTH_METHOD": "service_account",
                    "ALATION_CLIENT_ID": "id",
                    "ALATION_CLIENT_SECRET": "secret"
                }
            }
        }
    }
    ```

4. Save the file.

You can now use the MCP server in VSCode.

## Using MCP Tools in Agent Mode

Once you have added an MCP server, you can use the tools it provides in agent mode. To use MCP tools in agent mode:

1. Open the Chat view (⌃⌘I on macOS, Ctrl+Alt+I on Windows/Linux), and select **Agent mode** from the dropdown.

    ![Agent mode dropdown option](https://code.visualstudio.com/assets/docs/copilot/chat/mcp-servers/chat-mode-agent.png)

2. Select the **Tools** button to view the list of available tools.

    Optionally, select or deselect the tools you want to use. You can search tools by typing in the search box.

    ![MCP tools list](https://code.visualstudio.com/assets/docs/copilot/chat/mcp-servers/agent-mode-select-tools.png)

3. Enter a prompt in the chat input box. Tools will be automatically invoked as needed.

    By default, when a tool is invoked, you need to confirm the action before it is run. Use the **Continue** button dropdown options to automatically confirm the specific tool for the current session, workspace, or all future invocations.

    ![MCP Tool Confirmation](https://code.visualstudio.com/assets/docs/copilot/chat/mcp-servers/mcp-tool-confirmation.png)


You can now use the MCP tools effectively in agent mode.
