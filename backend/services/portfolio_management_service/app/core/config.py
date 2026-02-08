import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    INITIAL_CAPITAL: float = 100_000.0  # TND
    TRANSACTION_COST: float = 0.001     # 0.1 %
    RISK_FREE_RATE: float = 0.07        # 7 % — Tunisia TMM proxy

    TUNISIAN_TICKERS: list[str] = [
        "BIAT", "BH", "ATB", "STB",
        "SFBT", "UIB", "BNA", "ATTIJARI",
    ]

    # RL hyper-parameters
    RL_TIMESTEPS: int = 100_000
    RL_LEARNING_RATE: float = 3e-4
    RL_GAMMA: float = 0.99

    MODEL_DIR: str = "./models"
    DATA_DIR: str = "./data"

    # LLM
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    LLM_MODEL: str = "google/gemma-3-4b-it:free"
    LLM_MAX_TOKENS: int = 500

    # BCT fallback rates (updated when the site is unreachable)
    BCT_POLICY_RATE: float = 8.0
    BCT_TMM: float = 7.08
    BCT_SAVINGS_RATE: float = 6.0

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
