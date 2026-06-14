from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
class Settings(BaseSettings):
    DATABASE_URL: str
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env"
    )

settings = Settings()