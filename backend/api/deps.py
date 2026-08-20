from typing import AsyncGenerator
from fastapi import Depends, Request
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import settings
from core.exceptions import NotAuthorizedException
from database.session import get_db
from models.user import User

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise NotAuthorizedException("Could not validate credentials")
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise NotAuthorizedException("Could not validate credentials")
    except jwt.PyJWTError:
        raise NotAuthorizedException("Could not validate credentials")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise NotAuthorizedException("User not found")
        
    return user
