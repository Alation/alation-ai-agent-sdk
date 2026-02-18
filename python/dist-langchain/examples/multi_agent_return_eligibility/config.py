"""
Configuration settings for the minimal customer service agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Alation configuration
ALATION_BASE_URL = os.getenv("ALATION_BASE_URL")
ALATION_AUTH_METHOD = os.getenv("ALATION_AUTH_METHOD", "service_account")

# Initialize all variables to avoid ImportError
ALATION_CLIENT_ID = None
ALATION_CLIENT_SECRET = None

if ALATION_AUTH_METHOD == "service_account":
    ALATION_CLIENT_ID = os.getenv("ALATION_CLIENT_ID")
    ALATION_CLIENT_SECRET = os.getenv("ALATION_CLIENT_SECRET")
elif ALATION_AUTH_METHOD == "user_account":
    # This example currently only demonstrates service_account auth
    # For user_account implementation, see core-sdk examples
    raise ValueError(
        "This example currently only supports 'service_account' authentication. "
        "Please set ALATION_AUTH_METHOD=service_account in your .env file."
    )
else:
    raise ValueError(
        f"Invalid ALATION_AUTH_METHOD: {ALATION_AUTH_METHOD}. Must be 'service_account'."
    )

# LLM configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = 0.0

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Return policy settings
DEFAULT_RETURN_WINDOW_DAYS = 30
HIGH_VALUE_THRESHOLD = 1000  # Orders over $1000 may require review

USE_MOCK_DATA = "true"
