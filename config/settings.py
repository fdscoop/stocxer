"""
Configuration settings for TradeWise application
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Fyers API
    fyers_client_id: str
    fyers_secret_key: str
    fyers_redirect_uri: str = "http://localhost:8000/callback"
    fyers_access_token: Optional[str] = None
    
    # Database
    postgres_user: str = "tradewise"
    postgres_password: str
    postgres_db: str = "tradewise_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug_mode: bool = True
    
    # ML Configuration
    model_retrain_days: int = 7
    min_training_samples: int = 1000
    
    # Trading
    max_position_size: float = 100000.0
    risk_per_trade: float = 0.02
    default_symbol: str = "NSE:NIFTY"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/tradewise.log"
    
    @property
    def database_url(self) -> str:
        """Generate database URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Generate Redis URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
