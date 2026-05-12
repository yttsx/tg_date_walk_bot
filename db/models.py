from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    places: Mapped[list["Place"]] = relationship(back_populates="owner")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="user")
    routes: Mapped[list["GeneratedRoute"]] = relationship(back_populates="user")


class Place(Base):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(400), nullable=False)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    url: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    city: Mapped[str] = mapped_column(String(64), default="moscow")
    # private | group
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"))
    working_hours: Mapped[dict | None] = mapped_column(JSONB)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    # active | inactive | blacklisted
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="places")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="place")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    members: Mapped[list["GroupMember"]] = relationship(back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    # owner | member
    role: Mapped[str] = mapped_column(String(16), default="member")
    # accepted | pending
    status: Mapped[str] = mapped_column(String(16), default="accepted")

    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


class ScenarioTemplate(Base):
    __tablename__ = "scenario_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    participant_min: Mapped[int] = mapped_column(SmallInteger, default=1)
    participant_max: Mapped[int] = mapped_column(SmallInteger, default=99)
    steps_json: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class GeneratedRoute(Base):
    __tablename__ = "generated_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"))
    scenario_id: Mapped[int | None] = mapped_column(ForeignKey("scenario_templates.id"))
    places_json: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    distance_m: Mapped[int | None] = mapped_column(Integer)
    walk_minutes: Mapped[int | None] = mapped_column(Integer)
    total_minutes: Mapped[int | None] = mapped_column(Integer)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="routes")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="route")


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id"))
    route_id: Mapped[int | None] = mapped_column(ForeignKey("generated_routes.id"))
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1..5
    text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="ratings")
    place: Mapped["Place | None"] = relationship(back_populates="ratings")
    route: Mapped["GeneratedRoute | None"] = relationship(back_populates="ratings")
