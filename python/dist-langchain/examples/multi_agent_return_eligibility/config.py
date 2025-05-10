"""
Configuration settings for the minimal customer service agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Alation configuration
ALATION_BASE_URL = os.getenv("ALATION_BASE_URL")
ALATION_USER_ID = int(os.getenv("ALATION_USER_ID", "0"))
ALATION_REFRESH_TOKEN = os.getenv("ALATION_REFRESH_TOKEN")

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
