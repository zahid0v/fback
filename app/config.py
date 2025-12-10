from pydantic_settings import BaseSettings, SettingsConfigDict


_base_config = SettingsConfigDict(
    env_file="./.env",
    env_ignore_empty=True,
    extra="ignore",
)


class AppSettings(BaseSettings):
    APP_NAME: str = "FastShip"
    APP_DOMAIN: str = "localhost:8000"


class SecuritySettings(BaseSettings):

    JWT_SECRET: str
    JWT_ALGORITHM: str
    API_TOKEN: str
    ADMIN_TOKEN: str
    OPENPACK_TOKEN: str
    model_config = _base_config

app_settings = AppSettings()
security_settings = SecuritySettings()