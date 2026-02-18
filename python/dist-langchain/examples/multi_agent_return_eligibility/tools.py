from typing import List
import json
import sqlite3

from alation_ai_agent_langchain import (
    AlationAIAgentSDK,
    ServiceAccountAuthParams,
    get_langchain_tools,
)
from config import (
    ALATION_BASE_URL,
    ALATION_AUTH_METHOD,
    ALATION_CLIENT_ID,
    ALATION_CLIENT_SECRET,
)
from database import DB_PATH, init_database


def initialize_alation_sdk() -> AlationAIAgentSDK:
    """Initialize and return the Alation SDK instance."""
    if ALATION_AUTH_METHOD == "service_account":
        sdk = AlationAIAgentSDK(
            base_url=ALATION_BASE_URL,
            auth_method=ALATION_AUTH_METHOD,
            auth_params=ServiceAccountAuthParams(
                client_id=ALATION_CLIENT_ID, client_secret=ALATION_CLIENT_SECRET
            ),
        )
    else:
        raise ValueError(
            "Invalid ALATION_AUTH_METHOD. Must be 'user_account' or 'service_account'."
        )

    return sdk


def get_alation_tools() -> List:
    """Get LangChain tools from the Alation SDK."""
    sdk = initialize_alation_sdk()
    return get_langchain_tools(sdk)


def execute_sql(query: str) -> str:
    """
    Execute SQL query against the customer database.

    DEMONSTRATION PURPOSE: This function shows how LLMs can generate dynamic SQL
    based on natural language queries and Alation metadata. In production,
    implement proper SQL injection protection and access controls.

    Args:
        query: SQL query to execute

    Returns:
        JSON string with query results
    """
    # Basic safety check for demonstration purposes
    unsafe_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    for keyword in unsafe_keywords:
        if (
            keyword in query.upper()
            and keyword not in ["UPDATE"]
            and "WHERE" not in query.upper()
        ):
            return json.dumps(
                {
                    "error": f"Unsafe SQL operation: {keyword} without WHERE clause is not allowed"
                }
            )

    try:
        # Ensure database exists and has schema
        init_database()

        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()

        # Execute the query
        cursor.execute(query)

        # Fetch results
        results = [dict(row) for row in cursor.fetchall()]

        # Close connection
        conn.close()

        # Return results as JSON
        return json.dumps({"success": True, "results": results, "count": len(results)})

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
