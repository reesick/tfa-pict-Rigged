"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    app_name: str = "SmartFinance AI"
    debug: bool = True
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8081"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
