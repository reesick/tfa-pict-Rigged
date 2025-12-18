"""Application configuration using environment variables."""
import os
from functools import lru_cache
from typing import List


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Application Settings
        self.app_name: str = os.getenv("APP_NAME", "SmartFinance AI")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Database (Supabase PostgreSQL)
        self.database_url: str = os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:password@localhost:5432/postgres"
        )
        
        # Redis
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # ================== SUPABASE ==================
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")
        
        # Legacy JWT (for backward compat during migration)
        self.jwt_secret: str = os.getenv("JWT_SECRET", self.supabase_jwt_secret)
        self.jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )
        
        # ================== ML CONFIG ==================
        self.embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "768"))
        self.embedding_model: str = os.getenv("EMBEDDING_MODEL", "gemini-2.0-flash")
        
        # CORS
        self.cors_origins: str = os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:3000,http://localhost:8081,http://localhost:19006"
        )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_supabase_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.supabase_url and self.supabase_jwt_secret)


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

