"""
These mock implementations simulate Alation API responses for development and testing.

In a real implementation:
1. The data would come from your Alation catalog
2. The output structure (object type and its respective fields) will vary based on your signature.
3. Tag IDs and other filters would target your specific metadata

The mocks demonstrate the expected response format that your agents should handle.
"""

from typing import Dict, Any


def get_mock_customer_profile_metadata():
    """
    Return mock metadata for the vw_customer_profile view
    that would typically come from Alation.
    """
    return {
        "relevant_tables": [
            {
                "name": "vw_customer_profile",
                "title": "Customer Profile View",
                "description": "Consolidated view of customer information including contact details, shipping address, payment methods, and return history.",
                "url": "http://alation-instance/table/123",
                "columns": [
                    {
                        "name": "id",
                        "title": "Customer ID",
                        "description": "Unique identifier for the customer",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "name",
                        "title": "Customer Name",
                        "description": "Full name of the customer",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "email",
                        "title": "Email Address",
                        "description": "Primary email address for contacting the customer",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "status",
                        "title": "Account Status",
                        "description": "Current status of the customer account (active, inactive, suspended)",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "since",
                        "title": "Customer Since",
                        "description": "Date when the customer first registered",
                        "data_type": "DATE"
                    },
                    {
                        "name": "phone",
                        "title": "Phone Number",
                        "description": "Primary contact phone number",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "default_shipping_address",
                        "title": "Default Shipping Address",
                        "description": "Customer's preferred shipping address",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "preferred_payment_methods",
                        "title": "Preferred Payment Methods",
                        "description": "Comma-separated list of customer's payment methods",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "total_returns",
                        "title": "Total Returns",
                        "description": "Count of previous return requests by this customer",
                        "data_type": "INTEGER"
                    }
                ]
            }
        ]
    }


def get_mock_purchase_history_metadata():
    """
    Return mock metadata for the customer purchase history view.
    """
    return {
        "relevant_tables": [
            {
                "name": "vw_customer_purchase_history",
                "title": "Customer Purchase History View",
                "description": "Consolidated view of customer purchases",
                "url": "http://alation-instance/table/456",
                "columns": [
                    {
                        "name": "order_id",
                        "title": "Order ID",
                        "description": "Order ID",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "customer_id",
                        "title": "Customer ID",
                        "description": "Customer ID",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "order_date",
                        "title": "Order Date",
                        "description": "Order date",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "order_total",
                        "title": "Order Total",
                        "description": "Order total",
                        "data_type": "REAL"
                    },
                    {
                        "name": "order_item_id",
                        "title": "Order Item ID",
                        "description": "Line item ID",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "product_id",
                        "title": "Product ID",
                        "description": "Product ID",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "product_name",
                        "title": "Product Name",
                        "description": "Product name",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "product_category",
                        "title": "Product Category",
                        "description": "Product category",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "quantity",
                        "title": "Quantity",
                        "description": "Quantity purchased",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "unit_price",
                        "title": "Unit Price",
                        "description": "Unit price",
                        "data_type": "REAL"
                    },
                    {
                        "name": "line_total",
                        "title": "Line Total",
                        "description": "Total for this line",
                        "data_type": "REAL"
                    }
                ]
            }
        ]
    }


def get_mock_membership_benefits_metadata():
    """
    Return mock metadata for the customer membership benefits view.
    """
    return {
        "relevant_tables": [
            {
                "name": "vw_customer_membership_benefits",
                "title": "Customer Membership Benefits View",
                "description": "Details of customer membership tiers and associated benefits",
                "url": "http://alation-instance/table/789",
                "columns": [
                    {
                        "name": "customer_id",
                        "title": "Customer ID",
                        "description": "Customer ID",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "membership_tier",
                        "title": "Membership Tier",
                        "description": "Customer's membership level",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "enrollment_date",
                        "title": "Enrollment Date",
                        "description": "When customer enrolled in membership program",
                        "data_type": "DATE"
                    },
                    {
                        "name": "renewal_date",
                        "title": "Renewal Date",
                        "description": "Next renewal date",
                        "data_type": "DATE"
                    },
                    {
                        "name": "discount_percentage",
                        "title": "Discount Percentage",
                        "description": "Standard discount percentage",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "expedited_shipping",
                        "title": "Expedited Shipping",
                        "description": "Eligibility for free expedited shipping",
                        "data_type": "BOOLEAN"
                    },
                    {
                        "name": "extended_returns",
                        "title": "Extended Returns",
                        "description": "Extended return window in days",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "exclusive_events",
                        "title": "Exclusive Events",
                        "description": "Access to exclusive member events",
                        "data_type": "BOOLEAN"
                    },
                    {
                        "name": "reward_points_balance",
                        "title": "Reward Points Balance",
                        "description": "Current reward points balance",
                        "data_type": "INTEGER"
                    }
                ]
            }
        ]
    }


def get_mock_warranties_metadata():
    """
    Return mock metadata for the customer product warranties view.
    """
    return {
        "relevant_tables": [
            {
                "name": "vw_customer_product_warranties",
                "title": "Customer Product Warranties View",
                "description": "Active product warranties for customer purchases",
                "url": "http://alation-instance/table/567",
                "columns": [
                    {
                        "name": "warranty_id",
                        "title": "Warranty ID",
                        "description": "Warranty ID",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "customer_id",
                        "title": "Customer ID",
                        "description": "Customer ID",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "order_id",
                        "title": "Order ID",
                        "description": "Associated order ID",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "product_id",
                        "title": "Product ID",
                        "description": "Product ID",
                        "data_type": "INTEGER"
                    },
                    {
                        "name": "product_name",
                        "title": "Product Name",
                        "description": "Product name",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "warranty_type",
                        "title": "Warranty Type",
                        "description": "Standard or extended warranty",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "start_date",
                        "title": "Start Date",
                        "description": "Warranty start date",
                        "data_type": "DATE"
                    },
                    {
                        "name": "end_date",
                        "title": "End Date",
                        "description": "Warranty expiration date",
                        "data_type": "DATE"
                    },
                    {
                        "name": "coverage_details",
                        "title": "Coverage Details",
                        "description": "Summary of warranty coverage",
                        "data_type": "TEXT"
                    },
                    {
                        "name": "is_active",
                        "title": "Is Active",
                        "description": "Whether warranty is currently active",
                        "data_type": "BOOLEAN"
                    }
                ]
            }
        ]
    }


def get_mock_policy_electronics() -> Dict[str, Any]:
    """Return a detailed mock policy for electronics."""
    return {
        "documentation": {
            "title": "Electronics Return & Refund Policy",
            "content": (
                "General Rules:\n"
                "- Unopened electronics: full refund within 14 days of delivery.\n"
                "- Opened electronics: 15% restocking fee if returned within 7 days; no returns after 14 days unless defective.\n"
                "\nSpecial Categories:\n"
                "1. Batteries & Power Banks: returns only if sealed; no refunds for activated batteries.\n"
                "2. Software & Firmware: non-refundable once downloaded or registered.\n"
                "3. Accessories (cables, chargers): full refund within 30 days if unused and in original packaging.\n"
                "4. Wearables (smartwatches, headphones): returnable within 14 days; functional testing allowed; open-box fees may apply.\n"
                "\nDefective & Warranty Cases:\n"
                "- Returns for defects covered only if reported within 30 days with proof of purchase.\n"
                "- After 30 days, defective items cannot be returned but may be eligible for warranty service.\n"
                "- Manufacturer warranty valid up to 12 months for eligible items.\n"
                "\nMembership Benefits:\n"
                "- Silver tier: +15 days extended return window (29 days total)\n"
                "- Gold tier: +30 days extended return window (44 days total)\n"
                "\nHigh-Value Items:\n"
                "- Items over $500 require prior approval by customer service.\n"
                "\nExclusions & Conditions:\n"
                "- Missing original serial numbers or packaging voids return eligibility.\n"
                "- Liquid damage and physical abuse are not covered.\n"
            ),
            "url": "http://alation-instance/docs/electronics-return-policy"
        }
    }

def get_mock_policy_clothing() -> Dict[str, Any]:
    """Return a detailed mock policy for clothing items."""
    return {
        "documentation": {
            "title": "Clothing & Apparel Return Policy",
            "content": (
                "Return Timeframes:\n"
                "- Unworn clothing with tags: 45 days from delivery date for full refund.\n"
                "- Worn/washed clothing: Non-returnable except for manufacturing defects.\n"
                "- Swimwear and undergarments: Only returnable if hygiene seal is intact.\n"
                "\nSpecial Categories:\n"
                "1. Footwear: Eligible for return within 30 days if unworn/undamaged.\n"
                "2. Accessories (belts, hats, scarves): 45-day return window with original packaging.\n"
                "3. Seasonal items (winter coats, swimwear): Returns only within current season.\n"
                "\nMembership Benefits:\n"
                "- Bronze tier: +5 additional days to standard return window\n"
                "- Silver tier: +10 additional days to standard return window\n"
                "- Gold tier: +15 additional days to standard return window\n"
                "\nDefective Items:\n"
                "- Manufacturing defects covered within 90 days if reported promptly.\n"
                "\nHigh-Value Items:\n"
                "- Items over $500 require manager approval for returns.\n"
                "\nExclusions & Conditions:\n"
                "- Sale/clearance items marked 'final sale' not eligible for return.\n"
                "- Customized or altered items are non-returnable.\n"
            ),
            "url": "http://alation-instance/docs/clothing-return-policy"
        }
    }

def get_mock_policy_home_goods() -> Dict[str, Any]:
    """Return a detailed mock policy for home goods."""
    return {
        "documentation": {
            "title": "Home Goods & Furniture Return Policy",
            "content": (
                "Return Windows:\n"
                "- Small home goods (decor, kitchenware): 60 days from delivery for full refund.\n"
                "- Furniture (assembled): 30 days from delivery; 10% restocking fee applies.\n"
                "- Furniture (unassembled in original packaging): 60 days from delivery.\n"
                "\nSpecial Categories:\n"
                "1. Mattresses: 90-day comfort trial; one exchange allowed.\n"
                "2. Rugs & Carpets: 30 days if unused and in original packaging.\n"
                "3. Lighting fixtures: Non-returnable once installed; defects covered.\n"
                "4. Bedding & linens: Returnable within 30 days if unopened; non-returnable once used.\n"
                "\nMembership Benefits:\n"
                "- Bronze tier: Waived restocking fees up to $50\n"
                "- Silver tier: Waived restocking fees up to $100\n"
                "- Gold tier: Waived restocking fees up to $200 and free return shipping\n"
                "\nDefective & Warranty:\n"
                "- Manufacturing defects covered within 12 months.\n"
                "\nHigh-Value Items:\n"
                "- Items over $800 require approval for returns.\n"
                "- Items over $2000 require inspection before refund is issued.\n"
                "\nExclusions & Conditions:\n"
                "- Customized furniture not eligible for return.\n"
                "- Clearance items marked 'as-is' not returnable.\n"
                "- Customer responsible for return shipping on large items unless defective.\n"
            ),
            "url": "http://alation-instance/docs/home-goods-return-policy"
        }
    }


def mock_alation_context(question: str, signature=None):
    """
    Mock implementation of the Alation context tool.
    Handles requesting information about multiple tables in a single query.
    """
    q = question.lower()
    print(signature)
    response = {"relevant_tables": []}

    # Check for multi-table structure query
    if ("columns" in q or "structure" in q) and any(table in q for table in [
        "vw_customer_purchase_history",
        "vw_customer_membership_benefits",
        "vw_customer_product_warranties"
    ]):
        # Check which tables are included in the question
        if "vw_customer_purchase_history" in q:
            purchase_data = get_mock_purchase_history_metadata()
            response["relevant_tables"].extend(purchase_data["relevant_tables"])

        if "vw_customer_membership_benefits" in q:
            membership_data = get_mock_membership_benefits_metadata()
            response["relevant_tables"].extend(membership_data["relevant_tables"])

        if "vw_customer_product_warranties" in q:
            warranty_data = get_mock_warranties_metadata()
            response["relevant_tables"].extend(warranty_data["relevant_tables"])

        # If we added any tables, return the compiled response
        if response["relevant_tables"]:
            return response

    # Handle other specific cases
    if "vw_customer_profile" in q and ("columns" in q or "structure" in q):
        return get_mock_customer_profile_metadata()

    # Handle policy queries based on product categories
    if "policy" in q or "return" in q:
        # Electronics policies
        if any(term in q for term in ["electronics", "headphone", "tv", "speaker",
                                      "laptop", "computer", "phone", "camera"]):
            return get_mock_policy_electronics()

        # Clothing policies
        elif any(term in q for term in ["clothing", "apparel", "shirt", "pants",
                                        "dress", "shoes", "jacket", "sweater"]):
            return get_mock_policy_clothing()

        # Home goods policies
        elif any(term in q for term in ["home", "furniture", "decor", "kitchen",
                                        "mattress", "bedding", "rug"]):
            return get_mock_policy_home_goods()

    # Default fallback
    return {
        "message": "No specific mock data available for this query. This is a development mock.",
        "query": question
    }
