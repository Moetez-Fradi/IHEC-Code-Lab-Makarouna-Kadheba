"""
Configuration management for Carthage Alpha backend.
"""
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_title: str = "Carthage Alpha API"
    api_version: str = "1.0.0"
    api_description: str = "Intelligent Trading Assistant for BVMT"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/carthage_alpha"
    db_echo: bool = False
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5678"]
    
    # n8n Integration
    n8n_webhook_url: str = "http://localhost:5678/webhook"
    n8n_api_key: str = ""
    
    # ML Models
    model_path: str = "./models"
    sentiment_model_name: str = "UBC-NLP/MarBERT"
    prediction_model_path: str = "./models/prediction_model.pt"
    
    # External APIs
    news_api_key: str = ""
    bvmt_api_url: str = "https://www.bvmt.com.tn"
    
    # Redis (Optional)
    redis_url: str = "redis://localhost:6379/0"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
