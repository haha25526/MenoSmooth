"""
Admin auth for backstage
"""
from fastapi import Cookie, HTTPException, status
from typing import Optional

VALID_ADMIN_TOKEN = "meno-backstage-admin-token"


async def get_current_admin(token: Optional[str] = Cookie(None)) -> str:
    if token != VALID_ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return token


def verify_admin_password(password: str) -> bool:
    from backstage.app.config import settings
    return password == settings.ADMIN_PASSWORD
