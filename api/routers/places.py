from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.geocoder import geocode_address
from api.schemas import PlaceIn, PlaceOut
from core.database import get_session
from db.models import Place, User

router = APIRouter(prefix="/places", tags=["places"])

# Simplified to 3 categories matching scenario steps
TAG_RULES: dict[str, list[str]] = {
    "cafe": ["кофе", "кафе", "coffee", "cafe", "cappuccino", "latte", "bistro", "espresso"],
    "park": ["парк", "park", "сад", "garden", "бульвар", "природа", "набережная", "лес"],
    "food": ["еда", "food", "ресторан", "restaurant", "ужин", "dinner", "бар", "bar", "паб", "столовая"],
}


def _infer_tags(title: str, address: str, explicit_tags: list[str]) -> list[str]:
    if explicit_tags:
        return explicit_tags
    combined = (title + " " + address).lower()
    return [tag for tag, keywords in TAG_RULES.items() if any(kw in combined for kw in keywords)]


@router.post("", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
async def add_place(
    data: PlaceIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    tags = _infer_tags(data.title, data.address, data.tags)
    visibility = "group" if data.group_id else "private"

    lat, lon = data.lat, data.lon
    if not (lat and lon):
        coords = await geocode_address(data.address)
        if coords:
            lat, lon = coords

    place = Place(
        owner_id=user.id,
        title=data.title,
        address=data.address,
        url=data.url,
        lat=lat,
        lon=lon,
        tags=tags,
        working_hours=data.working_hours,
        city="moscow",
        group_id=data.group_id,
        visibility=visibility,
    )
    if lat and lon:
        place.geom = f"SRID=4326;POINT({lon} {lat})"
    session.add(place)
    await session.commit()
    await session.refresh(place)
    return place


@router.get("", response_model=list[PlaceOut])
async def list_places(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Place)
        .where(Place.owner_id == user.id, Place.status != "blacklisted")
        .order_by(Place.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def blacklist_place(
    place_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Place).where(Place.id == place_id, Place.owner_id == user.id)
    )
    place = result.scalar_one_or_none()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    place.status = "blacklisted"
    await session.commit()
