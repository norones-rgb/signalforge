from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SignalForge API"
    env: str = "dev"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    database_url: str = "postgresql+psycopg://signalforge:signalforge@postgres:5432/signalforge"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "change-me"
    fernet_key: str = "change-me"
    posting_disabled: bool = False
    admin_web_url: str = "http://localhost:3001"

    x_client_id: str | None = None
    x_client_secret: str | None = None
    x_oauth_redirect_uri: str = "http://localhost:8010/oauth/x/callback"
    x_oauth_scopes: str = "tweet.read tweet.write users.read offline.access"
    x_oauth_authorize_url: str = "https://x.com/i/oauth2/authorize"
    x_oauth_token_url: str = "https://api.x.com/2/oauth2/token"
    x_oauth_me_url: str = "https://api.x.com/2/users/me"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()
