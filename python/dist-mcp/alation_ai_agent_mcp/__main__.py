# Guard import to prevent multiprocessing issues on Windows
# The __main__.py module should only execute when run directly, not when imported
if __name__ == "__main__":
    from alation_ai_agent_mcp.server import run_server

    run_server()
