"""
API Dependencies
"""
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.core.security import verify_access_token
from app.core.exceptions import AuthenticationException, NotFoundException

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not credentials:
        raise AuthenticationException("Missing authentication credentials")
    token = credentials.credentials
    payload = verify_access_token(token)
    if not payload:
        raise AuthenticationException("Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Invalid token payload")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")
    if not user.is_active:
        raise AuthenticationException("User account is inactive")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
