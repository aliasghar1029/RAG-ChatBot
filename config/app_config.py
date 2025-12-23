import os
from typing import Optional
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    # API Keys
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    qdrant_url: str = os.getenv("QDRANT_URL", "")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    neon_db_url: str = os.getenv("NEON_DB_URL", "")
    sitemap_url: str = os.getenv("SITEMAP_URL", "")

    # Application settings
    app_title: str = os.getenv("APP_TITLE", "Docusaurus RAG Chatbot")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Qdrant settings
    qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "book_chunks")

    # Service availability
    cohere_enabled: bool = bool(os.getenv("COHERE_API_KEY", ""))
    qdrant_enabled: bool = bool(os.getenv("QDRANT_URL", "") and os.getenv("QDRANT_API_KEY", ""))
    openrouter_enabled: bool = bool(os.getenv("OPENROUTER_API_KEY", ""))
    database_enabled: bool = bool(os.getenv("NEON_DB_URL", ""))

    # Fallback settings
    enable_fallback_responses: bool = True
    fallback_message: str = "This information is not available in the book."
    service_timeout: int = int(os.getenv("SERVICE_TIMEOUT", "30"))  # seconds

    # Rate limiting
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # per minute
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

    # Caching
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = False

    def is_fully_configured(self) -> bool:
        """
        Check if all required services are properly configured
        """
        return all([
            self.cohere_enabled,
            self.qdrant_enabled,
            self.openrouter_enabled,
            self.database_enabled
        ])

    def get_available_services(self) -> dict:
        """
        Get a dictionary of which services are available
        """
        return {
            "cohere": self.cohere_enabled,
            "qdrant": self.qdrant_enabled,
            "openrouter": self.openrouter_enabled,
            "database": self.database_enabled
        }

# Global config instance
app_config = AppConfig()

# Validation
if not app_config.cohere_enabled:
    print("WARNING: Cohere API key not configured. Embedding functionality will be limited.")
if not app_config.qdrant_enabled:
    print("WARNING: Qdrant not configured. Vector storage functionality will be limited.")
if not app_config.openrouter_enabled:
    print("WARNING: OpenRouter API key not configured. LLM functionality will be limited.")
if not app_config.database_enabled:
    print("WARNING: Database URL not configured. Chat history will not be saved.")