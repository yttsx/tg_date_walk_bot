from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas import RatingIn, RatingOut
from core.database import get_session
from db.models import GeneratedRoute, Place, Rating, User

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("", response_model=RatingOut, status_code=201)
async def create_rating(
    data: RatingIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not data.place_id and not data.route_id:
        raise HTTPException(status_code=422, detail="Provide place_id or route_id")

    rating = Rating(
        user_id=user.id,
        place_id=data.place_id,
        route_id=data.route_id,
        value=data.value,
        text=data.text,
    )
    session.add(rating)

    # Update place rating aggregate
    if data.place_id:
        result = await session.execute(select(Place).where(Place.id == data.place_id))
        place = result.scalar_one_or_none()
        if place:
            total = place.rating_avg * place.rating_count + data.value
            place.rating_count += 1
            place.rating_avg = round(total / place.rating_count, 2)

    # Update route rating aggregate
    if data.route_id:
        result = await session.execute(
            select(GeneratedRoute).where(GeneratedRoute.id == data.route_id)
        )
        route = result.scalar_one_or_none()
        if route:
            # Simple: store last rating as avg (no count tracked on route)
            route.rating_avg = float(data.value)

    await session.commit()
    await session.refresh(rating)
    return rating


@router.get("/history", response_model=list[RatingOut])
async def rating_history(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Rating).where(Rating.user_id == user.id).order_by(Rating.created_at.desc())
    )
    return result.scalars().all()
