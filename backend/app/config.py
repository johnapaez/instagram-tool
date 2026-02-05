"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    database_url: str = "sqlite:///./instagram_tool.db"
    secret_key: str = "change-this-to-a-secure-random-string"
    cors_origins: str = "http://localhost:5173"
    max_daily_unfollows: int = 50
    min_action_delay: int = 30
    max_action_delay: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
