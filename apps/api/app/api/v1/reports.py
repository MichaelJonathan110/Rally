"""Report endpoints. Any authenticated user may file a report."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.schemas.moderation import ReportCreate, ReportRead
from app.services.moderation_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate, current_user: CurrentUser, db: DbSession
) -> ReportRead:
    """File a report against a user/activity/message/review/club/venue."""
    report = ReportService(db).create(
        current_user.id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        reason=payload.reason,
        details=payload.details,
    )
    return ReportRead.model_validate(report)
