from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserSchema(BaseModel):
    """
    Schema representing the data structure for creating a new user.

    Attributes:
        username (str): The username of the new user (up to 150 characters).
        email (EmailStr): The email address of the new user.
        password (str): The password of the new user (6 to 8 characters).

    Note:
        This schema is used for validating and parsing input data when creating a new user.
        It ensures that the provided data adheres to the specified format and constraints.
    """
    username: str = Field(max_length=150)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    """
    Schema representing the data structure for responding with details of a user.

    Attributes:
        id (int): The unique identifier of the user.
        username (str): The username of the user.
        email (EmailStr): The email address of the user.
        avatar (str): The URL of the user's avatar.

    Note:
        This schema is used for responding with details of a user, including its attributes.
        The `Config` class attribute is set to `from_attributes = True` to allow attribute-based instantiation.
    """
    id: int = 1
    username: str
    email: EmailStr
    avatar: str | None
    model_config = ConfigDict(from_attributes=True)  # noqa


class TokenSchema(BaseModel):
    """
    Schema representing the data structure for responding with authentication tokens.

    Attributes:
        access_token (str): The access token used for authenticating API requests.
        refresh_token (str): The refresh token used for obtaining a new access token.
        token_type (str): The type of token, defaults to "bearer".

    Note:
        This schema is used for responding with authentication tokens, including the access token,
        refresh token, and token type. It is typically used in the authentication flow.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    """
    Schema representing the data structure for requesting email-related operations.

    Attributes:
        email (EmailStr): The email address associated with the request.

    Note:
        This schema is used for validating and parsing input data when making email-related requests.
        It ensures that the provided email adheres to the specified format and constraints.
    """
    email: EmailStr
