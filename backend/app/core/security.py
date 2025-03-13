from passlib.context import CryptContext
from typing import Union, Any
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.conf.config import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: int = 15) -> str:
    """
    Creates the access token for the user for 15 minutes
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY_JWT, algorithm=config.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = 60 * 24 * 7) -> str:
    """
    Creates the refresh token for the user for 7 days
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY_JWT, algorithm=config.ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str) -> dict:
    """
    Decodes the JWT token, returns the payload of the token or raises an error
    """
    try:
        decoded = jwt.decode(token, config.SECRET_KEY_JWT, algorithms=[config.ALGORITHM])
        return decoded
    except JWTError:
        raise ValueError("Invalid token or token has expired")
