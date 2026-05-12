from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas import (
    GroupCreate,
    GroupMemberOut,
    GroupOut,
    InviteIn,
    InviteOut,
    MyGroupsOut,
)
from core.database import get_session
from db.models import Group, GroupMember, User

router = APIRouter(prefix="/groups", tags=["groups"])


async def _group_to_out(group: Group, session: AsyncSession) -> GroupOut:
    result = await session.execute(
        select(GroupMember, User)
        .join(User, User.id == GroupMember.user_id)
        .where(GroupMember.group_id == group.id)
    )
    members = [
        GroupMemberOut(
            user_id=member.user_id,
            telegram_id=user.telegram_id,
            username=user.username,
            role=member.role,
            status=member.status,
        )
        for member, user in result.all()
    ]
    return GroupOut(
        id=group.id,
        title=group.title,
        created_by=group.created_by,
        created_at=group.created_at,
        members=members,
    )


@router.post("", response_model=GroupOut, status_code=201)
async def create_group(
    data: GroupCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    group = Group(title=data.title, created_by=user.id)
    session.add(group)
    await session.flush()

    membership = GroupMember(
        group_id=group.id,
        user_id=user.id,
        role="owner",
        status="accepted",
    )
    session.add(membership)
    await session.commit()
    await session.refresh(group)
    return await _group_to_out(group, session)


@router.post("/invite", response_model=InviteOut)
async def invite_user(
    data: InviteIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Verify caller is accepted member of the group
    caller_membership = await session.get(GroupMember, (data.group_id, user.id))
    if not caller_membership or caller_membership.status != "accepted":
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    # Find invitee by username (strip leading @)
    username = data.username.lstrip("@")
    result = await session.execute(
        select(User).where(User.username == username)
    )
    invitee = result.scalar_one_or_none()
    if not invitee:
        raise HTTPException(
            status_code=404,
            detail="User not found. Ask them to write to the bot first.",
        )

    if invitee.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot invite yourself")

    # Check if already a member
    existing = await session.get(GroupMember, (data.group_id, invitee.id))
    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=409, detail="User is already in this group")
        # pending invite already exists — idempotent
        return InviteOut(
            group_id=data.group_id,
            invited_telegram_id=invitee.telegram_id,
            invited_username=invitee.username,
        )

    membership = GroupMember(
        group_id=data.group_id,
        user_id=invitee.id,
        role="member",
        status="pending",
    )
    session.add(membership)
    await session.commit()
    return InviteOut(
        group_id=data.group_id,
        invited_telegram_id=invitee.telegram_id,
        invited_username=invitee.username,
    )


@router.post("/{group_id}/accept", response_model=GroupOut)
async def accept_invite(
    group_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    membership = await session.get(GroupMember, (group_id, user.id))
    if not membership:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if membership.status == "accepted":
        raise HTTPException(status_code=409, detail="Already a member")

    membership.status = "accepted"
    await session.commit()

    group = await session.get(Group, group_id)
    return await _group_to_out(group, session)


@router.get("/my", response_model=MyGroupsOut)
async def my_groups(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(GroupMember, Group)
        .join(Group, Group.id == GroupMember.group_id)
        .where(GroupMember.user_id == user.id)
    )
    rows = result.all()

    accepted: list[GroupOut] = []
    pending: list[GroupOut] = []

    for membership, group in rows:
        group_out = await _group_to_out(group, session)
        if membership.status == "accepted":
            accepted.append(group_out)
        else:
            pending.append(group_out)

    return MyGroupsOut(accepted=accepted, pending=pending)
