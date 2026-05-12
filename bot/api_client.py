import aiohttp

from core.config import settings


def _headers(telegram_id: int) -> dict:
    return {"X-Telegram-Id": str(telegram_id)}


async def auth_user(telegram_id: int, username: str | None) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/auth/telegram",
            json={"telegram_id": telegram_id, "username": username},
        ) as r:
            r.raise_for_status()
            return await r.json()


async def add_place(telegram_id: int, payload: dict) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/places",
            json=payload,
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def list_places(telegram_id: int) -> list[dict]:
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{settings.API_BASE_URL}/places",
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def generate_route(telegram_id: int, scenario: str, group_id: int | None = None) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/routes/generate",
            json={"scenario": scenario, "group_id": group_id},
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def reroll_route(
    telegram_id: int, route_id: int, scenario: str, group_id: int | None = None
) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/routes/{route_id}/reroll",
            json={"scenario": scenario, "group_id": group_id},
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def post_rating(telegram_id: int, payload: dict) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/ratings",
            json=payload,
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def delete_place(telegram_id: int, place_id: int) -> None:
    async with aiohttp.ClientSession() as s:
        async with s.delete(
            f"{settings.API_BASE_URL}/places/{place_id}",
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()


async def get_history(telegram_id: int) -> list[dict]:
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{settings.API_BASE_URL}/history",
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def get_route(telegram_id: int, route_id: int) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{settings.API_BASE_URL}/routes/{route_id}",
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def create_group(telegram_id: int, title: str) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/groups",
            json={"title": title},
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def invite_to_group(telegram_id: int, group_id: int, username: str) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/groups/invite",
            json={"group_id": group_id, "username": username},
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def accept_group_invite(telegram_id: int, group_id: int) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/groups/{group_id}/accept",
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def join_group_by_link(telegram_id: int, group_id: int) -> dict:
    """Join group directly via invite link."""
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{settings.API_BASE_URL}/groups/{group_id}/join",
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def my_groups(telegram_id: int) -> dict:
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{settings.API_BASE_URL}/groups/my",
            headers=_headers(telegram_id),
        ) as r:
            r.raise_for_status()
            return await r.json()
