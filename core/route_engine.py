import math
import random
from datetime import datetime


# ~1.2 m/s average walking speed
WALK_SPEED_MPS = 1.2


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def walk_minutes(dist_m: float) -> int:
    return max(1, round(dist_m / WALK_SPEED_MPS / 60))


def _is_open_now(working_hours: dict | None) -> bool:
    """Return True if place is open. If no hours data — assume open."""
    if not working_hours:
        return True
    now = datetime.now()
    day_key = str(now.weekday())  # 0=Mon … 6=Sun
    hours = working_hours.get(day_key)
    if not hours:
        return False
    try:
        open_h, open_m = map(int, hours["open"].split(":"))
        close_h, close_m = map(int, hours["close"].split(":"))
        current_minutes = now.hour * 60 + now.minute
        open_minutes = open_h * 60 + open_m
        close_minutes = close_h * 60 + close_m
        return open_minutes <= current_minutes < close_minutes
    except Exception:
        return True


def _places_with_tag(places: list[dict], tags: list[str]) -> list[dict]:
    return [p for p in places if any(t in p.get("tags", []) for t in tags)]


def _place_has_coords(p: dict) -> bool:
    return p.get("lat") is not None and p.get("lon") is not None


def generate_route(
    steps: list[dict],
    candidate_places: list[dict],
    max_route_minutes: int = 120,
    max_radius_m: int = 3000,
    max_attempts: int = 10,
) -> dict | None:
    """
    Try up to max_attempts times to build a valid 3-stop route.
    Places without coordinates are allowed — distance/time are skipped for them.
    """
    active = [p for p in candidate_places if p.get("status", "active") == "active"]

    for _ in range(max_attempts):
        result = _try_generate(steps, active, max_route_minutes, max_radius_m)
        if result:
            return result
    return None


def _try_generate(
    steps: list[dict],
    places: list[dict],
    max_route_minutes: int,
    max_radius_m: int,
) -> dict | None:
    selected: list[dict] = []

    for i, step in enumerate(steps):
        candidates = _places_with_tag(places, step["tags"])
        candidates = [p for p in candidates if p not in selected]
        candidates = [p for p in candidates if _is_open_now(p.get("working_hours"))]

        # Apply radius filter only when both previous and current place have coords
        if i > 0 and selected and _place_has_coords(selected[-1]):
            prev = selected[-1]
            candidates = [
                p for p in candidates
                if not _place_has_coords(p)  # no coords → don't filter out
                or haversine_m(prev["lat"], prev["lon"], p["lat"], p["lon"]) <= max_radius_m
            ]

        if not candidates:
            return None

        selected.append(random.choice(candidates))

    # Compute totals only for places that have coordinates
    total_walk_m = 0
    total_walk_min = 0
    for j in range(1, len(selected)):
        if _place_has_coords(selected[j - 1]) and _place_has_coords(selected[j]):
            d = haversine_m(
                selected[j - 1]["lat"], selected[j - 1]["lon"],
                selected[j]["lat"], selected[j]["lon"],
            )
            total_walk_m += d
            total_walk_min += walk_minutes(d)

    activity_min = sum(s.get("duration_min", 0) for s in steps)
    total_minutes = total_walk_min + activity_min

    # Only enforce time limit if we actually calculated walk time
    if total_walk_min > 0 and total_minutes > max_route_minutes:
        return None

    return {
        "places": selected,
        "distance_m": round(total_walk_m) if total_walk_m else None,
        "walk_minutes": total_walk_min if total_walk_min else None,
        "total_minutes": total_minutes if total_walk_min else None,
        "yandex_url": _yandex_url(selected),
    }


def _yandex_url(places: list[dict]) -> str:
    coords = [p for p in places if _place_has_coords(p)]
    if not coords:
        # Fallback: search by address of first place
        first = places[0] if places else None
        if first:
            import urllib.parse
            q = urllib.parse.quote(first.get("address", ""))
            return f"https://yandex.ru/maps/213/moscow/?text={q}"
        return "https://yandex.ru/maps/213/moscow/"
    waypoints = "~".join(f"{p['lat']},{p['lon']}" for p in coords)
    return f"https://yandex.ru/maps/?rtext={waypoints}&rtt=pd"
