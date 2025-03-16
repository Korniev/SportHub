from pydantic.v1 import BaseSettings, EmailStr


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY_JWT: str
    ALGORITHM: str
    MAIL_USERNAME: EmailStr = "Jman-sorokolet@ukr.net"
    MAIL_PASSWORD: str = "Jenek251104"
    MAIL_FROM: str = "sporthub@email.com"
    MAIL_PORT: int = 567234
    MAIL_SERVER: str = "server"
    REDIS_DOMAIN: str = 'redis'
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    CLD_NAME: str = 'sporthub'
    CLP_API_KEY: int = 825412265738549
    CLD_API_SECRET: str = "key_secret"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()
