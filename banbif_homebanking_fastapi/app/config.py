from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "BanBif Home Banking"
    secret_key: str = "cambiar_esto"
    database_url: str = "sqlite:///./banbif.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
