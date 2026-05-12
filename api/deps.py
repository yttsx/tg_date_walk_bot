from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from db.models import User


async def get_current_user(
    x_telegram_id: int = Header(..., alias="X-Telegram-Id"),
    session: AsyncSession = Depends(get_session),
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == x_telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
