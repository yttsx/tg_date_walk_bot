from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas import RouteOut
from core.database import get_session
from core.route_engine import _yandex_url
from db.models import GeneratedRoute, User

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[RouteOut])
async def get_history(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(GeneratedRoute)
        .where(GeneratedRoute.user_id == user.id)
        .order_by(GeneratedRoute.created_at.desc())
        .limit(50)
    )
    routes = result.scalars().all()
    out = []
    for r in routes:
        url = _yandex_url(r.places_json) if r.places_json else ""
        out.append(
            RouteOut(
                id=r.id,
                user_id=r.user_id,
                scenario_id=r.scenario_id,
                places_json=r.places_json,
                distance_m=r.distance_m,
                walk_minutes=r.walk_minutes,
                total_minutes=r.total_minutes,
                rating_avg=r.rating_avg,
                yandex_url=url,
                created_at=r.created_at,
            )
        )
    return out
