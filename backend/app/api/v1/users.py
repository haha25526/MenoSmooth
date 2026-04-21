"""
User Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import uuid

from app.database import get_db
from app.api.deps import CurrentUser
from app.schemas import UserProfileUpdate, UserResponse
from app.config import settings
from app.models.user import User

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update: UserProfileUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    data = update.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(current_user, key, value)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)

@router.post("/avatar")
async def upload_avatar(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload avatar image"""
    static_dir = Path("/usr/share/nginx/meno/static/avatars")
    static_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{current_user.id}{ext}"
    filepath = static_dir / filename

    content = await file.read()
    filepath.write_bytes(content)

    avatar_url = f"/meno/static/avatars/{filename}"
    current_user.avatar = avatar_url
    await db.commit()

    return {"avatar": avatar_url}
