import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject, Update

from bot import api_client
from bot.handlers import groups, places, ratings, routes, start
from core.config import settings

logging.basicConfig(level=logging.INFO)


class AutoAuthMiddleware(BaseMiddleware):
    """Automatically register user on every update."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update: Update = data.get("event_update")
        user = None
        if update:
            if update.message:
                user = update.message.from_user
            elif update.callback_query:
                user = update.callback_query.from_user

        if user:
            try:
                await api_client.auth_user(user.id, user.username)
            except Exception:
                pass  # Don't block the update if auth fails

        return await handler(event, data)


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(AutoAuthMiddleware())

    dp.include_router(start.router)
    dp.include_router(places.router)
    dp.include_router(routes.router)
    dp.include_router(ratings.router)
    dp.include_router(groups.router)

    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
