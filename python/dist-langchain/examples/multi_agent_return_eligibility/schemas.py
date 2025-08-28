"""
State definitions and Alation signatures for the minimal customer service agent.
"""

from typing import Dict, List, Optional, Literal, Any
from typing_extensions import TypedDict


class CustomerState(TypedDict, total=False):
    """Simplified state shared between agents."""

    # Input data
    query: str
    email: Optional[str]

    # Retrieved information
    customer_info: Dict[str, Any]
    context_data: Dict[str, Any]
    policy_info: Dict[str, Any]

    # Decision
    eligibility_status: Optional[Literal["eligible", "ineligible", "unknown"]]
    requires_human: bool

    # Tracking
    current_phase: str
    agent_notes: List[str]

    # Response
    final_response: Optional[str]


# Alation Signatures

# Customer profile signature
CUSTOMER_PROFILE_SIGNATURE = {
    "table": {
        "fields_required": ["name", "title", "description", "url", "columns"],
        "search_filters": {
            "fields": {
                "tag_ids": [123]  # Replace with actual tag ID
            }
        },
        "child_objects": {
            "columns": {"fields": ["name", "title", "data_type", "description"]}
        },
    }
}

# Consolidated signature for customer data tables
CUSTOMER_DATA_SIGNATURE = {
    "table": {
        "fields_required": ["name", "title", "description", "url", "columns"],
        "search_filters": {
            "fields": {
                "tag_ids": [
                    456
                ]  # Single tag ID that covers all customer data tables ( These 3 views in our example
                # - "vw_customer_purchase_history", "vw_customer_membership_benefits",
                # "vw_customer_product_warranties")
            }
        },
        "child_objects": {
            "columns": {"fields": ["name", "title", "data_type", "description"]}
        },
    }
}

# Return policy signature
POLICY_SIGNATURE = {
    "documentation": {
        "fields_required": ["title", "content", "url"],
        "search_filters": {
            "fields": {
                "tag_ids": [789]  # Replace with actual tag ID
            }
        },
    }
}
