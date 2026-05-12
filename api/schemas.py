from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# --- Auth ---

class TelegramAuthIn(BaseModel):
    telegram_id: int
    username: str | None = None


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Places ---

class PlaceIn(BaseModel):
    title: str = Field(..., max_length=200)
    address: str = Field(..., max_length=400)
    url: str | None = Field(None, max_length=500)
    lat: float | None = None
    lon: float | None = None
    tags: list[str] = []
    working_hours: dict | None = None
    group_id: int | None = None


class PlaceOut(BaseModel):
    id: int
    owner_id: int
    title: str
    address: str
    url: str | None
    lat: float | None
    lon: float | None
    tags: list[str]
    city: str
    visibility: str
    group_id: int | None
    working_hours: dict | None
    rating_avg: float
    rating_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Routes ---

class RouteGenerateIn(BaseModel):
    scenario: str = Field(..., pattern="^(date|walk|light)$")
    group_id: int | None = None


class RouteRerollIn(BaseModel):
    scenario: str = Field(..., pattern="^(date|walk|light)$")
    group_id: int | None = None


class RouteOut(BaseModel):
    id: int
    user_id: int
    scenario_id: int | None
    places_json: list[dict]
    distance_m: int | None
    walk_minutes: int | None
    total_minutes: int | None
    rating_avg: float
    yandex_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Ratings ---

class RatingIn(BaseModel):
    place_id: int | None = None
    route_id: int | None = None
    value: int = Field(..., ge=1, le=5)
    text: str | None = None


class RatingOut(BaseModel):
    id: int
    user_id: int
    place_id: int | None
    route_id: int | None
    value: int
    text: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- History ---

class HistoryOut(BaseModel):
    routes: list[RouteOut]


# --- Groups ---

class GroupCreate(BaseModel):
    title: str = Field(..., max_length=200)


class InviteIn(BaseModel):
    group_id: int
    username: str = Field(..., max_length=64)


class GroupMemberOut(BaseModel):
    user_id: int
    telegram_id: int
    username: str | None
    role: str
    status: str


class GroupOut(BaseModel):
    id: int
    title: str
    created_by: int
    created_at: datetime
    members: list[GroupMemberOut] = []

    model_config = {"from_attributes": True}


class MyGroupsOut(BaseModel):
    accepted: list[GroupOut]
    pending: list[GroupOut]


class InviteOut(BaseModel):
    group_id: int
    invited_telegram_id: int
    invited_username: str | None
