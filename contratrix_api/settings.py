from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    ENV: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    CLOUDFLARE_ACCOUNT_ID: str
    CLOUDFLARE_ACCESS_KEY_ID: str
    CLOUDFLARE_SECRET_ACCESS_KEY: str
    CLOUDFLARE: str
    CLOUDFLARE_AVATAR: str
    BREVO_TOKEN: str
    BUCKET_NAME_TEMPLATES: str
    BUCKET_NAME_LOGOS: str
    BUCKET_NAME_AVATAR: str
    BUCKET_NAME_DOCUMENTOS: str

