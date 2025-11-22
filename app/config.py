from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5434
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "avito_backend"

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
    )

    @property
    def database_url_asyncpg(self):
        """URL для async подключения"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def database_url_psycopg(self):
        """URL для sync подключения (для миграций)"""
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"



settings = Settings()