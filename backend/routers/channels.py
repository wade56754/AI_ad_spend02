from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from core.db import get_db
from models import Channel, Log
from schemas import ChannelCreate, ChannelRead, ChannelUpdate

router = APIRouter(prefix="/api/channels", tags=["channels"])


def build_response(data, error=None):
    return {
        "data": data,
        "error": error,
        "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()},
    }


@router.get("/", response_model=dict)
def list_channels(db: Session = Depends(get_db)) -> dict:
    channels: List[Channel] = db.query(Channel).all()
    data = [ChannelRead.from_orm(channel).dict() for channel in channels]
    return build_response(data=data)


@router.get("/{channel_id}", response_model=dict)
def get_channel(channel_id: UUID, db: Session = Depends(get_db)) -> dict:
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    data = ChannelRead.from_orm(channel).dict()
    return build_response(data=data)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_channel(payload: ChannelCreate, db: Session = Depends(get_db)) -> dict:
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
    return build_response(data=data)


@router.put("/{channel_id}", response_model=dict)
def update_channel(channel_id: UUID, payload: ChannelUpdate, db: Session = Depends(get_db)) -> dict:
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
    return build_response(data=data)


