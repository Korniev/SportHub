import pickle
from datetime import datetime, timedelta
from typing import Optional

import redis
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.database.db import get_db
from app.reposiroty import users as repository_users
from app.conf.config import config


class Auth:
    """
    Utility class for handling authentication-related operations.

    Attributes:
        pwd_context (CryptContext): Password hashing context.
        SECRET_KEY (str): Secret key used for JWT encoding and decoding.
        ALGORITHM (str): JWT algorithm used for encoding and decoding.
        cache (redis.Redis): Redis cache for storing user information.

    Note:
        This class provides methods for password hashing, token generation, and user authentication.
        It also includes functions for decoding refresh tokens, retrieving the current user from an access token,
        creating an email verification token, and extracting the email from an email verification token.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, db=0, encoding="utf-8",
                        password=config.REDIS_PASSWORD)

    def verify_password(self, plain_password, hashed_password):
        """
        Verify a plaintext password against a hashed password.

        Args:
            plain_password (str): The plaintext password.
            hashed_password (str): The hashed password.

        Returns:
            bool: True if the plaintext password matches the hashed password, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Generate a hashed password.

        Args:
            password (str): The plaintext password.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Generate a new access token.

        Args:
            data (dict): Data to be encoded in the token.
            expires_delta (float, optional): Expiration time for the token in seconds.

        Returns:
            str: The encoded access token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Generate a new refresh token.

        Args:
           data (dict): Data to be encoded in the token.
           expires_delta (float, optional): Expiration time for the token in seconds.

        Returns:
           str: The encoded refresh token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_form_refresh_token(self, refresh_token: str):
        """
        Decode a refresh token to retrieve the email.

        Args:
            refresh_token (str): The encoded refresh token.

        Returns:
            str: The email retrieved from the token.

        Raises:
            HTTPException: If the token is invalid or the scope is incorrect.
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        """
        Retrieve the current user based on the provided access token.

        Args:
            token (str, optional): The access token.
            db (AsyncSession, optional): The asynchronous database session.

        Returns:
            User: The current user.

        Raises: HTTPException: If the token is invalid, the scope is incorrect, or the user cannot be retrieved from
        the cache or database.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user_hash = str(email)
        user = self.cache.get(user_hash)

        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            await self.cache.set(user_hash, pickle.dumps(user))
            await self.cache.expire(user_hash, 300)
        else:
            user = pickle.loads(user)

        return user

    def create_email_token(self, data: dict):
        """
        Create a JWT token for email verification.

        Args:
            data (dict): Data to be encoded in the token.

        Returns:
            str: The encoded JWT token.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=1)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
        Decode a JWT token to retrieve the email for email verification.

        Args:
           token (str): The JWT token.

        Returns:
           str: The email retrieved from the token.

        Raises:
           HTTPException: If the token is invalid or the email cannot be extracted.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")


auth_service = Auth()