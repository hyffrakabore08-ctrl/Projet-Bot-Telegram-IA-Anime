import os

# Telegram Bot Token (from HF Secrets)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Hugging Face API Token (from HF Secrets)
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# Admin User ID (from HF Secrets) - restrict access to this user
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# AniList GraphQL API URL
ANILIST_API_URL = "https://graphql.anilist.co"

# Database path (persistent storage on HF Spaces)
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/app.db")

# Hugging Face Model for IA Agent
HF_MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"

# Score weights for anime ranking
SCORE_WEIGHT_LIKES = 0.5
SCORE_WEIGHT_VIEWS = 0.3
SCORE_WEIGHT_COMMENTS = 0.2

# Timezone for scheduling
TIMEZONE = "UTC"

# Debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# FastAPI host and port (HF Spaces requires 7860)
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 7860
