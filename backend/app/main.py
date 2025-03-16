import re
from typing import Callable

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.routers import auth, users, protected_router

app = FastAPI()

app.include_router(protected_router.router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_agent_ban_list = [r"Googlebot", r"Python-urllib"]

app.include_router(auth.router, prefix='/auth')
app.include_router(users.router, prefix='/users')


@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    """
    Middleware to check the user-agent header for banned patterns.

    Args:
        request (Request): The incoming HTTP request.
        call_next (Callable): The function to call to proceed with the request.

    Returns:
        JSONResponse: If a banned user-agent pattern is detected, returns a 403 Forbidden response.
                      Otherwise, proceeds with the request.

    Note:
        This middleware checks the user-agent header against a list of banned patterns.
        If a match is found, it returns a 403 Forbidden response; otherwise, it allows the request to proceed.
    """
    user_agent = request.headers.get("user-agent")
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response


@app.get("/test")
def index():
    """
    Endpoint for testing purposes.

    Returns:
        dict: A simple message indicating the success of the endpoint.
    """
    return {"message": "Test"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
   Endpoint to check the health of the application and database connection.

   Args:
       db (AsyncSession): The asynchronous database session.

   Returns:
       dict: A message indicating the health status of the application and database.

   Raises:
       HTTPException: If an error occurs while connecting to the database, a 500 Internal Server Error is raised.
   """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to SportHub!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
