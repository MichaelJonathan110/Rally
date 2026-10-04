"""Check-in endpoints.

A participant checks in to an activity (within its window); the host can list
everyone who has checked in.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.core.exceptions import PermissionDeniedError
from app.schemas.checkin import CheckInCreate, CheckInRead
from app.services.activity_service import ActivityService
from app.services.checkin_service import CheckInService

router = APIRouter(prefix="/activities", tags=["check-in"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/{activity_id}/checkin",
    response_model=CheckInRead,
    status_code=status.HTTP_201_CREATED,
)
def check_in(
    activity_id: uuid.UUID,
    payload: CheckInCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> CheckInRead:
    """Check the caller in to an activity (participants only, in-window)."""
    checkin = CheckInService(db).check_in(
        activity_id,
        current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        method=payload.method,
    )
    return CheckInRead.model_validate(checkin)


@router.get("/{activity_id}/checkins", response_model=list[CheckInRead])
def list_checkins(
    activity_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> list[CheckInRead]:
    """List check-ins for an activity (host only)."""
    activity = ActivityService(db).get(activity_id)
    if activity.host_id != current_user.id:
        raise PermissionDeniedError("Only the host may view check-ins")
    rows = CheckInService(db).list_checkins(activity_id)
    return [CheckInRead.model_validate(c) for c in rows]
