from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas import RouteGenerateIn, RouteOut
from core.config import settings
from core.database import get_session
from core.route_engine import generate_route
from db.models import GeneratedRoute, GroupMember, Place, ScenarioTemplate, User

router = APIRouter(prefix="/routes", tags=["routes"])


async def _get_scenario(name: str, session: AsyncSession) -> ScenarioTemplate:
    result = await session.execute(
        select(ScenarioTemplate).where(ScenarioTemplate.name == name, ScenarioTemplate.active.is_(True))
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    return scenario


async def _get_candidates(
    user: User, session: AsyncSession, group_id: int | None = None
) -> list[dict]:
    if group_id:
        # Group route: places explicitly shared with this group (from any accepted member)
        members_result = await session.execute(
            select(GroupMember.user_id).where(
                GroupMember.group_id == group_id,
                GroupMember.status == "accepted",
            )
        )
        member_ids = [row[0] for row in members_result.all()]
        if not member_ids:
            member_ids = [user.id]
        where_clause = (
            Place.owner_id.in_(member_ids),
            Place.group_id == group_id,
            Place.status == "active",
            Place.city == "moscow",
        )
    else:
        # Solo route: all of user's own places regardless of visibility
        where_clause = (
            Place.owner_id == user.id,
            Place.status == "active",
            Place.city == "moscow",
        )

    result = await session.execute(
        select(Place).where(*where_clause)
    )
    places = result.scalars().all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "address": p.address,
            "lat": p.lat,
            "lon": p.lon,
            "url": p.url,
            "tags": p.tags or [],
            "working_hours": p.working_hours,
            "status": p.status,
        }
        for p in places
    ]


def _route_to_out(route_record: GeneratedRoute, yandex_url: str) -> RouteOut:
    return RouteOut(
        id=route_record.id,
        user_id=route_record.user_id,
        scenario_id=route_record.scenario_id,
        places_json=route_record.places_json,
        distance_m=route_record.distance_m,
        walk_minutes=route_record.walk_minutes,
        total_minutes=route_record.total_minutes,
        rating_avg=route_record.rating_avg,
        yandex_url=yandex_url,
        created_at=route_record.created_at,
    )


@router.get("/{route_id}", response_model=RouteOut)
async def get_route(
    route_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    route = await session.get(GeneratedRoute, route_id)
    if not route or route.user_id != user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Route not found")
    from core.route_engine import _yandex_url
    return _route_to_out(route, _yandex_url(route.places_json))


@router.post("/generate", response_model=RouteOut)
async def generate(
    data: RouteGenerateIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    scenario = await _get_scenario(data.scenario, session)
    candidates = await _get_candidates(user, session, data.group_id)

    result = generate_route(
        steps=scenario.steps_json,
        candidate_places=candidates,
        max_route_minutes=settings.MAX_ROUTE_MINUTES,
        max_radius_m=settings.MAX_RADIUS_M,
        max_attempts=settings.MAX_REROLL_ATTEMPTS,
    )
    if not result:
        raise HTTPException(status_code=422, detail="Could not generate a valid route. Add more places.")

    route_record = GeneratedRoute(
        user_id=user.id,
        group_id=data.group_id,
        scenario_id=scenario.id,
        places_json=result["places"],
        distance_m=result["distance_m"],
        walk_minutes=result["walk_minutes"],
        total_minutes=result["total_minutes"],
    )
    session.add(route_record)
    await session.commit()
    await session.refresh(route_record)
    return _route_to_out(route_record, result["yandex_url"])


@router.post("/{route_id}/reroll", response_model=RouteOut)
async def reroll(
    route_id: int,
    data: RouteGenerateIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    scenario = await _get_scenario(data.scenario, session)
    all_candidates = await _get_candidates(user, session, data.group_id)

    # Try to exclude places from the previous route for variety
    prev = await session.get(GeneratedRoute, route_id)
    candidates = all_candidates
    if prev and prev.user_id == user.id:
        used_ids = {p["id"] for p in prev.places_json}
        without_used = [c for c in all_candidates if c["id"] not in used_ids]
        # Only exclude if enough candidates remain per step
        candidates = without_used if without_used else all_candidates

    result = generate_route(
        steps=scenario.steps_json,
        candidate_places=candidates,
        max_route_minutes=settings.MAX_ROUTE_MINUTES,
        max_radius_m=settings.MAX_RADIUS_M,
        max_attempts=settings.MAX_REROLL_ATTEMPTS,
    )
    # Fallback: retry with full pool if excluding previous places blocked generation
    if not result and candidates is not all_candidates:
        result = generate_route(
            steps=scenario.steps_json,
            candidate_places=all_candidates,
            max_route_minutes=settings.MAX_ROUTE_MINUTES,
            max_radius_m=settings.MAX_RADIUS_M,
            max_attempts=settings.MAX_REROLL_ATTEMPTS,
        )
    if not result:
        raise HTTPException(status_code=422, detail="Could not generate a new route. Add more places.")

    route_record = GeneratedRoute(
        user_id=user.id,
        group_id=data.group_id,
        scenario_id=scenario.id,
        places_json=result["places"],
        distance_m=result["distance_m"],
        walk_minutes=result["walk_minutes"],
        total_minutes=result["total_minutes"],
    )
    session.add(route_record)
    await session.commit()
    await session.refresh(route_record)
    return _route_to_out(route_record, result["yandex_url"])
