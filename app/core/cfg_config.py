from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FIREBASE_WEB_API_KEY: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    PORT: int = 8010
    DATABASE_URL: str = ""
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8010"
    ENV: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY no configurada. "
                "Define SECRET_KEY en .env o como variable de entorno. "
                "Genera una clave con: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL no configurada. "
                "Define DATABASE_URL en .env o como variable de entorno."
            )

settings = Settings()
