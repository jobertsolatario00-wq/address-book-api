"""Application settings, overridable through environment variables."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./address_book.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
