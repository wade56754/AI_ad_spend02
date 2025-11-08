from math import ceil
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import ok
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import Channel, Log
from backend.schemas import ChannelCreate, ChannelRead, ChannelUpdate

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("/", response_model=dict)
def list_channels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Channel)

    if is_active is not None:
        query = query.filter(Channel.is_active == is_active)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(Channel.name.ilike(like_pattern))

    total = query.count()
    items: List[Channel] = (
        query.order_by(Channel.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = [ChannelRead.from_orm(channel).dict() for channel in items]
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if page_size else 0,
    }
    return ok(data=data, meta={"pagination": pagination})


@router.get("/{channel_id}", response_model=dict)
def get_channel(
    channel_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    data = ChannelRead.from_orm(channel).dict()
    return ok(data=data, status_code=status.HTTP_201_CREATED)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_channel(
    payload: ChannelCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    channel = Channel(**payload.dict())
    db.add(channel)
    db.flush()

    log_entry = Log(
        actor_id=payload.created_by,
        action="create_channel",
        target_table="channels",
        target_id=channel.id,
        before_data=None,
        after_data=jsonable_encoder(ChannelRead.from_orm(channel)),
    )
    db.add(log_entry)

    db.commit()
    db.refresh(channel)
    data = ChannelRead.from_orm(channel).dict()
    return ok(data=data)


@router.put("/{channel_id}", response_model=dict)
def update_channel(
    channel_id: UUID,
    payload: ChannelUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    before_state = jsonable_encoder(ChannelRead.from_orm(channel))

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(channel, key, value)

    log_entry = Log(
        actor_id=update_data.get("updated_by"),
        action="update_channel",
        target_table="channels",
        target_id=channel.id,
        before_data=before_state,
        after_data=None,
    )
    db.add(log_entry)

    db.flush()
    db.refresh(channel)
    log_entry.after_data = jsonable_encoder(ChannelRead.from_orm(channel))

    db.commit()
    db.refresh(channel)

    data = ChannelRead.from_orm(channel).dict()
    return ok(data=data)


