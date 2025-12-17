"""Application configuration using environment variables."""
import os
from functools import lru_cache
from typing import List


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Application Settings
        self.app_name: str = os.getenv("APP_NAME", "SmartFinance AI")
        self.debug: bool = os.getenv("DEBUG", "True").lower() == "true"
        
        # Database
        self.database_url: str = os.getenv(
            "DATABASE_URL", 
            "postgresql://financeuser:financepass@localhost:5432/financedb"
        )
        
        # Redis
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # JWT Configuration
        self.jwt_secret: str = os.getenv(
            "JWT_SECRET", 
            "default-secret-key-change-in-production-minimum-32-chars"
        )
        self.jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )
        self.refresh_token_expire_days: int = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")
        )
        
        # CORS
        self.cors_origins: str = os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:3000,http://localhost:8081"
        )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


_settings = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    """Reset settings for testing."""
    global _settings
    _settings = None
