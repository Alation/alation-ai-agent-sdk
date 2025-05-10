from typing import List
import json
import sqlite3

from alation_ai_agent_langchain import AlationAIAgentSDK, get_langchain_tools
from config import ALATION_BASE_URL, ALATION_USER_ID, ALATION_REFRESH_TOKEN
from database import DB_PATH, init_database


def initialize_alation_sdk() -> AlationAIAgentSDK:
    """Initialize and return the Alation SDK instance."""
    sdk = AlationAIAgentSDK(
        base_url=ALATION_BASE_URL,
        user_id=ALATION_USER_ID,
        refresh_token=ALATION_REFRESH_TOKEN
    )

    return sdk


def get_alation_tools() -> List:
    """Get LangChain tools from the Alation SDK."""
    sdk = initialize_alation_sdk()
    return get_langchain_tools(sdk)


def execute_sql(query: str) -> str:
    """
    Execute SQL query against the customer database.

    Args:
        query: SQL query to execute

    Returns:
        JSON string with query results
    """
    # Check if query is safe - in production, implement proper SQL injection protection
    unsafe_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
    for keyword in unsafe_keywords:
        if keyword in query.upper() and keyword not in ['UPDATE'] and 'WHERE' not in query.upper():
            return json.dumps({
                "error": f"Unsafe SQL operation: {keyword} without WHERE clause is not allowed"
            })

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
        return json.dumps({
            "success": True,
            "results": results,
            "count": len(results)
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })
