from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.users import User, UserPreference
from app.schemas.common import UserPreferencesOut, UserPreferencesUpdate
from app.services.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/preferences", response_model=UserPreferencesOut)
async def get_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user.id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        return UserPreferencesOut()
    return UserPreferencesOut.model_validate(prefs)


@router.patch("/me/preferences")
async def update_preferences(
    body: UserPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user.id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
    if body.theme_json is not None:
        prefs.theme_json = body.theme_json
    if body.account_json is not None:
        prefs.account_json = body.account_json
    if body.filters_json is not None:
        prefs.filters_json = body.filters_json
    prefs.updated_at = datetime.now(UTC)
    await db.flush()
    return {"ok": True}
