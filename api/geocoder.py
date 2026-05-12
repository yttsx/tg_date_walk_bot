import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

_YANDEX_GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"


async def geocode_address(address: str) -> tuple[float, float] | None:
    """Return (lat, lon) for address via Yandex Geocoder, or None on failure."""
    if not settings.YANDEX_MAPS_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                _YANDEX_GEOCODER_URL,
                params={"apikey": settings.YANDEX_MAPS_API_KEY, "geocode": address, "format": "json"},
            )
            resp.raise_for_status()
            members = (
                resp.json()
                .get("response", {})
                .get("GeoObjectCollection", {})
                .get("featureMember", [])
            )
            if not members:
                return None
            pos: str = members[0]["GeoObject"]["Point"]["pos"]
            lon_str, lat_str = pos.split()
            return float(lat_str), float(lon_str)
    except Exception as exc:
        logger.warning("Geocoding failed for %r: %s", address, exc)
        return None
