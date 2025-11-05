from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    slack_manager_user_id: str
    
    # Database
    database_url: str
    
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()