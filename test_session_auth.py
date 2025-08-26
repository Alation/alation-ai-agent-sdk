#!/usr/bin/env python3
"""
Simple test script to test SessionAuthParams with cookie authentication
and the get_context tool.

Usage:
1. Update the configuration variables in the CONFIG section below
2. Run: python test_session_auth.py

Prerequisites:
- Your Alation instance must be accessible
- You need a valid session cookie from your browser
"""

import sys
import os

# Add the core-sdk to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python", "core-sdk"))

from alation_ai_agent_sdk import AlationAIAgentSDK, SessionAuthParams

# "SESSION_COOKIE": "_ga=GA1.1.1945945304.1725860682; _ga_S9PQDTJJE3=GS1.1.1740878149.4.1.1740879381.0.0.0; i18nextNeo=en; fs_uid=#14YKVY#c0d2f575-f621-4a39-9348-810a07b72788:1126ef96-fe09-4856-9319-d905780c8d1d:1753737079804::2#/1769644683; sessionid=idmuvzsd9ymg619to8zjxh1sq7hq61kt; csrftoken=NIObk6SKQOJKRhgiwr9dsfbrml0fuW0m; jwt_session=eyJhbGciOiJSUzI1NiIsImtpZCI6ImY2MmU1OTExLWY4N2UtNDQwMi1hNmEyLWRjZWJlNDRjMWY2YiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTYyOTAxMzUsImZjX3VzZXJfaWQiOiI5OCIsImlhbV91c2VyX3JvbGVfaWQiOjEsImlhbV91c2VyX3V1aWQiOiI2MzQ5NjhlNy04N2UyLTRjYWItYmE4YS1lZjhmNWRiM2UyZmMiLCJpYXQiOjE3NTYyNDY5MzYsImlzcyI6ImFsYXRpb24uY29tIiwianRpIjoiNGI2OTI5NzgtMjIzMS00NWFmLWFhNTktNmZhMWIyNzA0NTY4IiwibmJmIjoxNzU2MjQ2OTM2LCJzdWIiOiJhZG1pbkBhbGF0aW9uLmNvbSIsInRlbmFudF91cmwiOiJodHRwczovL2dlbmFpLWdhcnRuZXIubXRzZS5hbGF0aW9uY2xvdWQuY29tIiwidXNlcl9yb2xlIjoiU2VydmVyIEFkbWluIiwidXNlcl9zZXNzaW9uX2tleSI6ImlkbXV2enNkOXltZzYxOXRvOHpqeGgxc3E3aHE2MWt0In0.JOYTq6TYp4oHHccjIRddgwcRLSxZMmQRTNJOZYjDAl7aMXtMIPgHLpKA0mCOXEPp9Es7NqjKvN3BgMou7e6jbKDUtdqxUhYq-w_CqOg_F_0jXLgsifGAG0xXuQK3T1Z5OafRCzadm_YSEsNmL_MjOCxe2RjGGRE74ZubcY53diKNcXAYPYswRwicUCy9UgM2dx4EdkSBK8elcSqeG01be0EqtYiFoiQVDUmwuWXoICw08PmeO1jOqVcMke96O5-dzQxGBSpom0TVOvGdmHLIizvxPu-72zH9RJLUHX29GVzaYjjgHwOJdCsdj6a5qM_ShYtbaHsIKrkSWadJp2G_Dg",
# ===== CONFIGURATION =====
# Update these values for your Alation instance
CONFIG = {
    "BASE_URL": "https://genai-gartner.mtse.alationcloud.com",
    "SESSION_COOKIE": "_ga=GA1.1.1945945304.1725860682; _ga_S9PQDTJJE3=GS1.1.1740878149.4.1.1740879381.0.0.0; i18nextNeo=en; fs_uid=#14YKVY#c0d2f575-f621-4a39-9348-810a07b72788:1126ef96-fe09-4856-9319-d905780c8d1d:1753737079804::2#/1769644683; sessionid=idmuvzsd9ymg619to8zjxh1sq7hq61kt; csrftoken=NIObk6SKQOJKRhgiwr9dsfbrml0fuW0m; jwt_session=eyJhbGciOiJSUzI1NiIsImtpZCI6ImY2MmU1OTExLWY4N2UtNDQwMi1hNmEyLWRjZWJlNDRjMWY2YiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTYyOTAxMzUsImZjX3VzZXJfaWQiOiI5OCIsImlhbV91c2VyX3JvbGVfaWQiOjEsImlhbV91c2VyX3V1aWQiOiI2MzQ5NjhlNy04N2UyLTRjYWItYmE4YS1lZjhmNWRiM2UyZmMiLCJpYXQiOjE3NTYyNDY5MzYsImlzcyI6ImFsYXRpb24uY29tIiwianRpIjoiNGI2OTI5NzgtMjIzMS00NWFmLWFhNTktNmZhMWIyNzA0NTY4IiwibmJmIjoxNzU2MjQ2OTM2LCJzdWIiOiJhZG1pbkBhbGF0aW9uLmNvbSIsInRlbmFudF91cmwiOiJodHRwczovL2dlbmFpLWdhcnRuZXIubXRzZS5hbGF0aW9uY2xvdWQuY29tIiwidXNlcl9yb2xlIjoiU2VydmVyIEFkbWluIiwidXNlcl9zZXNzaW9uX2tleSI6ImlkbXV2enNkOXltZzYxOXRvOHpqeGgxc3E3aHE2MWt0In0.JOYTq6TYp4oHHccjIRddgwcRLSxZMmQRTNJOZYjDAl7aMXtMIPgHLpKA0mCOXEPp9Es7NqjKvN3BgMou7e6jbKDUtdqxUhYq-w_CqOg_F_0jXLgsifGAG0xXuQK3T1Z5OafRCzadm_YSEsNmL_MjOCxe2RjGGRE74ZubcY53diKNcXAYPYswRwicUCy9UgM2dx4EdkSBK8elcSqeG01be0EqtYiFoiQVDUmwuWXoICw08PmeO1jOqVcMke96O5-dzQxGBSpom0TVOvGdmHLIizvxPu-72zH9RJLUHX29GVzaYjjgHwOJdCsdj6a5qM_ShYtbaHsIKrkSWadJp2G_Dg",
    "TEST_QUERY": "What tables contain customer information?",  # Test query for the context API
}


def test_session_auth():
    """Test SessionAuthParams with a sample query using get_context."""

    # Get configuration
    BASE_URL = CONFIG["BASE_URL"]
    SESSION_COOKIE = CONFIG["SESSION_COOKIE"]
    TEST_QUERY = CONFIG["TEST_QUERY"]

    print("🚀 Testing SessionAuthParams with get_context tool")
    print("=" * 60)

    try:
        # Initialize the SDK with session authentication
        print(f"📡 Connecting to: {BASE_URL}")
        print(f"🍪 Using session cookie: {SESSION_COOKIE[:20]}...")

        sdk = AlationAIAgentSDK(
            base_url=BASE_URL,
            auth_method="session",
            auth_params=SessionAuthParams(session_cookie=SESSION_COOKIE),
        )

        print("✅ SDK initialized successfully with session authentication")
        print()

        res = sdk.get_data_products(query="arr")
        resp = sdk.check_job_status(job_id=12)
        print(resp)
        print(res)

        # Test the alation_context tool
        print(f"🔍 Testing query: '{TEST_QUERY}'")
        print("📊 Calling get_context...")

        result = sdk.get_context(question=TEST_QUERY)

        print("✅ get_context call successful!")
        print()
        print("📋 Results:")
        print("-" * 40)

        # Pretty print the results
        if isinstance(result, dict):
            for key, value in result.items():
                if key == "results" and isinstance(value, list):
                    print(f"{key}: {len(value)} items")
                    # Show first few items
                    for i, item in enumerate(value[:3]):
                        print(f"  [{i+1}] {type(item).__name__}: {str(item)[:100]}...")
                else:
                    print(f"{key}: {str(value)[:200]}...")
        else:
            print(str(result)[:500])

        print()
        print("🎉 Test completed successfully!")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        print(f"Error type: {type(e).__name__}")

        # Check if it's an authentication issue
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            print()
            print("💡 Troubleshooting tips:")
            print("1. Make sure your session cookie is valid and not expired")
            print("2. Verify the BASE_URL is correct")
            print("3. Check that you have access to the Alation instance")
            print("4. Try logging into the Alation UI first to refresh your session")

        return False

    return True


def get_session_cookie_instructions():
    """Print instructions on how to get a session cookie."""
    print("🍪 How to get your session cookie:")
    print("=" * 50)
    print("1. Open your browser and go to your Alation instance")
    print("2. Log in to Alation")
    print("3. Open browser Developer Tools (F12)")
    print("4. Go to the 'Application' or 'Storage' tab")
    print("5. Under 'Cookies', find your Alation domain")
    print("6. Look for 'sessionid' cookie and copy its value")
    print("7. Format it as: 'sessionid=your_cookie_value_here'")
    print()
    print("Alternative method using Network tab:")
    print("1. Open Developer Tools > Network tab")
    print("2. Refresh the page")
    print("3. Click on any request to your Alation instance")
    print("4. Look at Request Headers > Cookie")
    print("5. Copy the entire Cookie header value")
    print()


def test_other_tools():
    """Test other SDK tools that should work with session auth."""
    BASE_URL = CONFIG["BASE_URL"]
    SESSION_COOKIE = CONFIG["SESSION_COOKIE"]

    try:
        sdk = AlationAIAgentSDK(
            base_url=BASE_URL,
            auth_method="session",
            auth_params=SessionAuthParams(session_cookie=SESSION_COOKIE),
        )

        print("🧪 Testing other SDK tools with session auth:")
        print("-" * 50)

        # Test bulk_retrieval
        print("📦 Testing get_bulk_objects...")
        signature = {"table": {"fields_required": ["name", "url"], "limit": 5}}
        bulk_result = sdk.get_bulk_objects(signature=signature)
        print(f"✅ get_bulk_objects: Retrieved {len(bulk_result.get('results', []))} tables")

        # Test check_job_status (this should fail with session auth)
        print("⚠️  Testing check_job_status (should fail with session auth)...")
        try:
            sdk.check_job_status(job_id=123)
            print("❌ Unexpected: check_job_status should have failed")
        except Exception as e:
            if "Session authentication is not supported" in str(e):
                print("✅ Expected: check_job_status correctly blocked session auth")
            else:
                print(f"❓ Unexpected error: {e}")

        print("🎉 Additional tools testing completed!")

    except Exception as e:
        print(f"❌ Error testing additional tools: {e}")


if __name__ == "__main__":
    print("Alation AI Agent SDK - Session Authentication Test")
    print("=" * 60)
    print()

    # Check if configuration looks like it needs updating
    test_url = CONFIG["BASE_URL"]
    test_cookie = CONFIG["SESSION_COOKIE"]

    if "your-instance" in test_url or "your_session_cookie" in test_cookie:
        print("⚠️  Configuration needed!")
        print()
        get_session_cookie_instructions()
        print("Please update the configuration values in the CONFIG section of this file")
        print("and run the test again.")
        print()
        exit(1)

    # Run the main test
    success = test_session_auth()

    if success:
        print()
