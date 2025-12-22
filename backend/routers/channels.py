from math import ceil
from typing import List, Optional
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.logging import log_requests
from backend.core.response import success_response, error_response
from backend.core.error_codes import BusinessErrorCodes
from backend.core.dependencies import get_current_user
from backend.models import User
from backend.models import Channel, Log
from backend.schemas import ChannelCreate, ChannelRead, ChannelUpdate

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=dict)
@log_requests("channels")
def list_channels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Channel)

    # is_active 映射到 status 列
    if is_active is not None:
        status_value = 'active' if is_active else 'inactive'
        query = query.filter(Channel.status == status_value)

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
    data = [ChannelRead.model_validate(channel, from_attributes=True).model_dump() for channel in items]
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if page_size else 0,
    }
    return success_response(data={"items": data, "meta": {"pagination": pagination}}, message="获取渠道列表成功")


@router.get("/{channel_id}", response_model=dict)
@log_requests("channels")
def get_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message="渠道不存在",
            status_code=404
        )
    data = ChannelRead.model_validate(channel, from_attributes=True).model_dump()
    return success_response(data=data)


@router.post("", response_model=dict, status_code=201)
@log_requests("channels")
def create_channel(
    payload: ChannelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    # 使用 model_dump() 获取数据 (Pydantic v2)
    channel_data = payload.model_dump(exclude_unset=True)

    # 确保有默认状态
    if 'status' not in channel_data or not channel_data['status']:
        channel_data['status'] = 'active'

    # 手动生成 UUID（避免依赖 PostgreSQL 的 gen_random_uuid 函数）
    channel_data['id'] = uuid4()

    channel = Channel(**channel_data)
    db.add(channel)
    db.flush()

    log_entry = Log(
        id=str(uuid4()),  # Log.id 是 String(36)
        actor_id=str(current_user.id) if current_user else None,
        action="create_channel",
        target_table="channels",
        target_id=str(channel.id),
        before_data=None,
        after_data=jsonable_encoder(ChannelRead.model_validate(channel, from_attributes=True).model_dump()),
    )
    db.add(log_entry)

    db.commit()
    db.refresh(channel)
    data = ChannelRead.model_validate(channel, from_attributes=True).model_dump()
    return success_response(data=data, message="渠道创建成功", status_code=201)


@router.put("/{channel_id}", response_model=dict)
@log_requests("channels")
def update_channel(
    channel_id: UUID,
    payload: ChannelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message="渠道不存在",
            status_code=404
        )

    # 记录更新前状态
    before_state = jsonable_encoder(ChannelRead.model_validate(channel, from_attributes=True).model_dump())

    # 获取更新数据 (Pydantic v2)
    update_data = payload.model_dump(exclude_unset=True)

    # 更新字段（跳过只读属性）
    for key, value in update_data.items():
        if hasattr(channel, key) and not isinstance(getattr(type(channel), key, None), property):
            setattr(channel, key, value)

    db.flush()
    db.refresh(channel)

    # 记录更新后状态
    after_state = jsonable_encoder(ChannelRead.model_validate(channel, from_attributes=True).model_dump())

    log_entry = Log(
        id=str(uuid4()),
        actor_id=str(current_user.id) if current_user else None,
        action="update_channel",
        target_table="channels",
        target_id=str(channel.id),
        before_data=before_state,
        after_data=after_state,
    )
    db.add(log_entry)

    db.commit()
    db.refresh(channel)

    data = ChannelRead.model_validate(channel, from_attributes=True).model_dump()
    return success_response(data=data, message="渠道更新成功")


