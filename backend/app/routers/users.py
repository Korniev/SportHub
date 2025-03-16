import pickle

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository import users as repository_users
from app.database.db import get_db
from app.entity.models import User
from app.schemas.auth import UserResponse
from app.services.auth import auth_service
from app.conf.config import config

router = APIRouter(prefix='/users', tags=['users'])
cloudinary.config(cloud_name=config.CLD_NAME, api_key=config.CLP_API_KEY, api_secret=config.CLD_API_SECRET, secure=True)


@router.get("/me", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_current_user(current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve details of the currently authenticated user.

    Args:
        current_user (User): The current authenticated user.

    Returns:
        UserResponse: The response containing details of the authenticated user.

    Note:
        The endpoint retrieves details of the currently authenticated user and returns them in the response.
    """
    return current_user


@router.patch("/avatar", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_avatar(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                        db: AsyncSession = Depends(get_db)):
    """
    Update the avatar of the currently authenticated user with the provided image file.

    Args:
        file (UploadFile): The image file to be used as the new avatar.
        current_user (User): The current authenticated user.
        db (AsyncSession): The asynchronous database session.

    Returns:
        UserResponse: The response containing details of the updated user with the new avatar.

    Note:
        The endpoint uploads the provided image file to Cloudinary, updates the avatar URL for the currently
        authenticated user in the database, refreshes the user to get updated database state, and then returns
        the details of the updated user. The user's information is also cached for 300 seconds.
    """
    public_id = f"contact_book/{current_user.email}"
    res = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(width=250, height=250, crop="fill",
                                                              version=res.get("version"))
    current_user = await repository_users.update_avatar_url(current_user.email, res_url, db)
    auth_service.cache.set(current_user.email, pickle.dumps(current_user))
    auth_service.cache.expire(current_user.email, 300)
    return current_user
