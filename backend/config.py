"""
Configuration module for the AI-CRM HCP Module.

Loads environment variables and provides a centralized Settings class
for all application configuration values.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables with sensible defaults.

    Attributes:
        APP_NAME: Display name of the application.
        APP_VERSION: Current semantic version string.
        DEBUG: Enables debug mode when True.
        DATABASE_URL: SQLAlchemy-compatible database connection string.
        GROQ_API_KEY: API key for the Groq LLM service.
        GROQ_MODEL: Model identifier to use with Groq (default: llama-3.1-8b-instant).
        GROQ_TEMPERATURE: Sampling temperature for LLM responses.
        GROQ_MAX_TOKENS: Maximum tokens in LLM response.
        CORS_ORIGINS: Comma-separated list of allowed CORS origins.
        API_PREFIX: URL prefix for all API routes.
        HOST: Host address to bind the server to.
        PORT: Port number to bind the server to.
    """

    APP_NAME: str = os.getenv("APP_NAME", "AI-CRM HCP Module")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./crm_hcp.db")

    # Groq LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.3"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "2048"))

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    # API
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list of origin strings."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
