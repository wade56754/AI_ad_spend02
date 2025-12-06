from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from backend.models import Log


class LogService:
    @staticmethod
    def write(
        db: Session,
        *,
        action: str,
        operator_id: Optional[str],
        target: str,
        detail: Dict[str, Any],
        target_id: Optional[UUID] = None,
    ) -> None:
        if operator_id is None:
            return
        try:
            operator_uuid = UUID(operator_id)
        except (TypeError, ValueError):
            return
        entry = Log(
            id=str(uuid4()),
            actor_id=str(operator_uuid),
            action=action,
            target_table=target,
            target_id=str(target_id) if target_id else None,
            before_data=None,
            after_data=jsonable_encoder(detail),
            created_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()

