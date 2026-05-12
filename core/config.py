from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    BOT_USERNAME: str = ""  # @username бота без @ — для генерации ссылок-приглашений
    API_BASE_URL: str = "http://api:8000"

    DATABASE_URL: str
    DATABASE_SYNC_URL: str

    YANDEX_MAPS_API_KEY: str = ""
    SECRET_KEY: str = "change_me"

    # Route constraints
    MAX_ROUTE_MINUTES: int = 300
    MAX_RADIUS_M: int = 10000
    MAX_REROLL_ATTEMPTS: int = 10


settings = Settings()
