"""Administrative + moderation endpoints.

Every route here is gated by ``require_roles`` - a server-side dependency. A
caller without the required role is rejected with 403 before the handler body
executes; the frontend is never the authorization boundary. Destructive
actions (role change, ban/unban, report resolution) are ADMIN-only and always
write a row to the moderation action log.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.enums import ModerationActionType, ReportStatus, UserRole
from app.models.user import User
from app.schemas.common import Page
from app.schemas.moderation import (
    BanRequest,
    ModerationActionRead,
    ReportRead,
    ReportResolveRequest,
    RoleChangeRequest,
)
from app.schemas.user import UserRead
from app.services.moderation_service import ModerationService, ReportService

router = APIRouter(prefix="/admin", tags=["admin"])

DbSession = Annotated[Session, Depends(get_db)]

# Moderators and admins may list users/reports; only admins may mutate.
ModeratorGate = Annotated[User, Depends(require_roles(UserRole.MODERATOR))]
AdminGate = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


# --- users -----------------------------------------------------------------
@router.get("/users", response_model=Page[UserRead])
def list_users(
    _gate: ModeratorGate,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[UserRead]:
    """Paginated user list. Requires MODERATOR or ADMIN."""
    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(
        select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch("/users/{user_id}/role", response_model=UserRead)
def change_role(
    user_id: uuid.UUID, payload: RoleChangeRequest, gate: AdminGate, db: DbSession
) -> UserRead:
    """Change a user's role. ADMIN only; logged to the moderation action log."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == gate.id and payload.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot demote yourself",
        )
    previous = user.role
    user.role = payload.role
    db.add(user)
    db.commit()
    db.refresh(user)
    ModerationService(db).log_action(
        gate.id,
        action=ModerationActionType.WARN,
        target_user_id=user.id,
        reason=f"Role changed {previous} -> {payload.role}",
    )
    return UserRead.model_validate(user)


@router.post("/users/{user_id}/ban", response_model=ModerationActionRead)
def ban_user(
    user_id: uuid.UUID, payload: BanRequest, gate: AdminGate, db: DbSession
) -> ModerationActionRead:
    """Ban (deactivate) a user. ADMIN only."""
    action = ModerationService(db).ban_user(
        user_id, gate.id, reason=payload.reason, duration_hours=payload.duration_hours
    )
    return ModerationActionRead.model_validate(action)


@router.post("/users/{user_id}/unban", response_model=ModerationActionRead)
def unban_user(
    user_id: uuid.UUID, gate: AdminGate, db: DbSession, reason: str | None = None
) -> ModerationActionRead:
    """Unban (reactivate) a user. ADMIN only."""
    action = ModerationService(db).unban_user(user_id, gate.id, reason=reason)
    return ModerationActionRead.model_validate(action)


# --- reports ---------------------------------------------------------------
@router.get("/reports", response_model=Page[ReportRead])
def list_reports(
    _gate: ModeratorGate,
    db: DbSession,
    status_filter: Annotated[ReportStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ReportRead]:
    """List reports. Requires MODERATOR or ADMIN."""
    rows, total = ReportService(db).list_reports(
        status=status_filter, limit=limit, offset=offset
    )
    return Page[ReportRead](
        items=[ReportRead.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/reports/{report_id}/resolve", response_model=ReportRead)
def resolve_report(
    report_id: uuid.UUID,
    payload: ReportResolveRequest,
    gate: AdminGate,
    db: DbSession,
) -> ReportRead:
    """Resolve or dismiss a report. ADMIN only; logs the action."""
    report = ReportService(db).resolve(
        report_id,
        gate.id,
        status=payload.status,
        note=payload.note,
        action=payload.action,
    )
    return ReportRead.model_validate(report)


# --- moderation log --------------------------------------------------------
@router.get("/moderation-actions", response_model=Page[ModerationActionRead])
def list_moderation_actions(
    _gate: ModeratorGate,
    db: DbSession,
    target_user_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ModerationActionRead]:
    """The moderation action audit log. Requires MODERATOR or ADMIN."""
    rows, total = ModerationService(db).list_actions(
        target_user_id=target_user_id, limit=limit, offset=offset
    )
    return Page[ModerationActionRead](
        items=[ModerationActionRead.model_validate(a) for a in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/ping")
def admin_ping(_gate: AdminGate) -> dict[str, str]:
    """Trivial admin-only probe used to prove the role gate is enforced."""
    return {"status": "admin_ok"}
