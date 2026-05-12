from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import TelegramAuthIn, UserOut
from core.database import get_session
from db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=UserOut)
async def telegram_auth(data: TelegramAuthIn, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.telegram_id == data.telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=data.telegram_id, username=data.username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    elif data.username and user.username != data.username:
        user.username = data.username
        await session.commit()
        await session.refresh(user)
    return user
