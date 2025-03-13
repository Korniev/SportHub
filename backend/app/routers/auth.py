from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.db import get_db
from app.entity.models import User
from app.schemas.auth_schemas import UserRegister, UserLogin, TokenSchema, TokenRefresh
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_jwt
)
from app.conf.config import config

router = APIRouter(tags=["Authentication"], prefix="/auth")


@router.post("/signup", response_model=dict)
async def signup(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password=hashed_pw,
        username=user_data.username,
        role="user"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"message": "User created", "user_id": new_user.id}


@router.post("/login", response_model=TokenSchema)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalar()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(subject=user.email, expires_delta=15)
    refresh_token = create_refresh_token(subject=user.email, expires_delta=60*24*7)

    user.refresh_token = refresh_token
    await db.commit()
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(body: TokenRefresh, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_jwt(body.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_email = payload.get("sub")  # тут "sub" = user.email
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    stmt = select(User).where(User.email == user_email)
    result = await db.execute(stmt)
    user = result.scalar()
    if not user or user.refresh_token != body.refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found or mismatch")

    new_access = create_access_token(subject=user.email, expires_delta=15)
    new_refresh = create_refresh_token(subject=user.email, expires_delta=60*24*7)

    user.refresh_token = new_refresh
    await db.commit()

    return Token(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(db: AsyncSession = Depends(get_db), token: str = Depends(...)):
    """
    Якщо хочемо “відкликати” поточний refresh_token,
    треба якось визначити користувача.
    """
    # Залежно від логіки – можна декодувати access_token,
    # знайти user, обнулити refresh_token:
    raise HTTPException(status_code=501, detail="Not implemented yet")
