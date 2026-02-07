import os
from typing import List, Union, Dict
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- SERVER CONFIG ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "info"

    # --- INFO PROJET ---
    PROJECT_NAME: str = "BVMT Sentiment Analysis API"
    API_V1_STR: str = "/api/v1"

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # --- OPENROUTER / LLM CONFIG ---
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "") 
    OPENROUTER_MODEL: str = "tngtech/deepseek-r1t2-chimera:free"

    # --- TICKER KEYWORDS (C'est ce qui manquait !) ---
    # Dictionnaire : { "TICKER": ["Synonyme1", "Synonyme2", ...] }
    TICKER_KEYWORDS: Dict[str, List[str]] = {
        "SFBT": ["SFBT", "Boissons de Tunisie", "Société de Fabrication des Boissons de Tunisie", "Bière"],
        "BIAT": ["BIAT", "Banque Internationale Arabe de Tunisie"],
        "BNA": ["BNA", "Banque Nationale Agricole"],
        "BT": ["BT", "Banque de Tunisie"],
        "SAH": ["SAH", "Lilas"],
        "SOTUVER": ["SOTUVER", "Verreries"],
        "CARTHAGE": ["CARTHAGE", "Carthage Cement"],
        "POULINA": ["POULINA", "PGH", "Poulina Group Holding"],
        "DELICE": ["DELICE", "Delice Holding", "Danone"],
        "EURO-CYCLES": ["EURO-CYCLES", "Euro Cycles"],
        "SMART": ["SMART", "Smart Tunisie"],
        "TELNET": ["TELNET", "Telnet Holding"],
        "TUNISAIR": ["TUNISAIR", "Tunis Air", "TU"],
    }

    # --- CONFIG LOADING ---
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()