from fastapi import Depends
from gravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.entity.models import User
from app.schemas.auth_schemas import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a user by their email address.

    Args:
        email (str): The email address of the user to retrieve.
        db (AsyncSession): The asynchronous database session.

    Returns:
        User or None: The retrieved user if found, or None if no matching user is found.

    Note:
        The function performs an asynchronous database query to retrieve a user based on their email address.
        If a matching user is found, it is returned; otherwise, None is returned.
    """
    statement = select(User).filter_by(email=email)
    user = await db.execute(statement)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
        Create a new user with the provided user data.

        Args:
            body (UserSchema): The user data used for creating the new user.
            db (AsyncSession): The asynchronous database session.

        Returns:
            User: The newly created user.

        Note:
            The function performs an asynchronous database transaction to create a new user with the provided data.
            It generates a Gravatar avatar for the user based on their email address (if available), adds the user
            to the database, commits the transaction, refreshes the user to get updated database state, and then
            returns the newly created user.
        """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    Update the refresh token for a user.

    Args:
        user (User): The user for whom the refresh token is being updated.
        token (str | None): The new refresh token, or None to remove the refresh token.
        db (AsyncSession): The asynchronous database session.

    Returns:
        None

    Note:
        The function updates the refresh token for the specified user and commits the changes to the database.
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Confirm the email address for a user.

    Args:
        email (str): The email address of the user to confirm.
        db (AsyncSession): The asynchronous database session.

    Returns:
        None

    Note:
        The function performs an asynchronous database query to retrieve a user by email, sets the 'confirmed'
        attribute to True, and then commits the changes to the database.
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession):
    """
       Update the avatar URL for a user.

       Args:
           email (str): The email address of the user whose avatar URL is being updated.
           url (str | None): The new avatar URL, or None to remove the avatar URL.
           db (AsyncSession): The asynchronous database session.

       Returns:
           User: The updated user with the new avatar URL.

       Note:
           The function performs an asynchronous database query to retrieve a user by email, updates the 'avatar'
           attribute with the new URL, commits the changes to the database, refreshes the user to get updated
           database state, and then returns the updated user.
       """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user
