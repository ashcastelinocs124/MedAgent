# conftest.py — root-level pytest configuration
# Loads .env so DATABASE_URL, OPENAI_API_KEY, etc. are available during test collection.
from dotenv import load_dotenv

load_dotenv()
