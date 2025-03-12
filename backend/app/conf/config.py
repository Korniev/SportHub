from typing import Any

from pydantic import ConfigDict, field_validator, EmailStr
from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY_JWT: str
    ALGORITHM: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()
