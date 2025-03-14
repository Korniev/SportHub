from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.repository import users as repository_users
from app.schemas.user import UserSchema, UserResponse
from app.services import auth
from app.services.email import send_email
from app.conf import messages

router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@router.get('/refresh_token')
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    """
    Refresh the access token using a valid refresh token.

    Args:
        credentials (HTTPAuthorizationCredentials): The HTTP authorization credentials containing the refresh token.
        db (AsyncSession): The asynchronous database session.

    Returns:
        dict: A dictionary containing the new access token, refresh token, and token type.

    Raises:
        HTTPException: If the provided refresh token is invalid or expired, a 401 Unauthorized response is raised.

    Note:
        The endpoint verifies the provided refresh token, retrieves the corresponding user by decoding the token,
        checks if the stored refresh token matches the provided token, and then generates a new access token and
        refresh token pair. If successful, the user's refresh token is updated in the database, and the new tokens
        are returned. If the refresh token is invalid, a 401 Unauthorized response is raised.
    """
    token = credentials.credentials
    email = await auth_service.decode_form_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    """
        Register a new user account.

        Args:
            body (UserSchema): The user data used for creating the new user.
            bt (BackgroundTasks): Background tasks to be executed after a successful registration.
            request (Request): The incoming HTTP request.
            db (AsyncSession): The asynchronous database session.

        Returns:
            UserResponse: The response containing the details of the newly created user.

        Raises:
            HTTPException: If the provided email is already associated with an existing account,
            a 409 Conflict response is raised.

        Note:
            The endpoint checks if the provided email is already associated with an existing account.
            If not, it creates a new user with the provided data, hashes the password, and stores the user
            in the database. After successful registration, a confirmation email is scheduled to be sent
            using background tasks. The response includes the details of the newly created user.
        """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXISTS)
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user and generate access and refresh tokens.

    Args:
        body (OAuth2PasswordRequestForm): The user credentials (email and password) for authentication.
        db (AsyncSession): The asynchronous database session.

    Returns:
        dict: A dictionary containing the access token, refresh token, and token type.

    Raises:
        HTTPException: If the provided email is not found, the email is not confirmed,
        or the password is invalid, a 401 Unauthorized response is raised.

    Note:
        The endpoint authenticates the user by verifying the email, confirmed status, and password.
        If successful, it generates a new access token and refresh token pair. The user's refresh token
        is updated in the database, and the tokens are returned in the response.
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_EMAIL)
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.NOT_CONFIRMED)
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_PASSWORD)
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
       Confirm a user's email using a confirmation token.

       Args:
           token (str): The confirmation token received by the user.
           db (AsyncSession): The asynchronous database session.

       Returns:
           dict: A dictionary containing a confirmation message.

       Raises:
           HTTPException: If the provided token is invalid or the user's email is already confirmed,
           a 400 Bad Request response is raised.

       Note:
           The endpoint verifies the provided confirmation token, retrieves the corresponding user by decoding
           the token, checks if the user's email is already confirmed, and then updates the user's 'confirmed'
           attribute in the database. A confirmation message is returned in the response.
       """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.VERIFICATION_ERROR)
    if user.confirmed:
        return {"message": messages.EMAIL_CONFIRMED_ERROR}
    await repository_users.confirmed_email(email, db)
    return {"message": messages.EMAIL_CONFIRMED}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    Send a confirmation email to the user to request email confirmation.

    Args:
        body (RequestEmail): The user's email for requesting confirmation.
        background_tasks (BackgroundTasks): Background tasks to be executed for sending the confirmation email.
        request (Request): The incoming HTTP request.
        db (AsyncSession): The asynchronous database session.

    Returns:
        dict: A dictionary containing a confirmation message.

    Note:
        The endpoint checks if the user's email is already confirmed. If not, it retrieves the user by email,
        and if the user exists, a confirmation email is scheduled to be sent using background tasks.
        A confirmation message is returned in the response.
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": messages.EMAIL_CONFIRMED_ERROR}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": messages.CHECK_EMAIL}