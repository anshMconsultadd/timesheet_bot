from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    slack_manager_user_id: str
    # Excluded users who don't need to fill timesheets (comma-separated user IDs)
    # Example: U12345ABC,U67890XYZ
    excluded_user_ids: str = ""
    # Reminder posting delay (seconds) between first reminder and posting channel-wide missing users list
    # In production this should be 3600 (1 hour). For local testing you can set to 120 (2 minutes).
    reminder_post_delay_seconds: int = 3600
    
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