"""Activity endpoints: CRUD, discovery filters, join/leave, participants.

RALLY is sports-only: activities are created against a SPORT from the sports
catalog (``sport_slug``), and can be discovered by sport or sport category
(racket/team/combat/...). Join/leave are real capacity state changes - a full
activity waitlists the joiner, and leaving promotes the next waiter.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.models.enums import ActivityCategory, NotificationType, SkillLevel, SportCategory
from app.schemas.activity import (
    ActivityCreate,
    ActivityParticipantRead,
    ActivityRead,
    ActivityUpdate,
    MyActivitiesRead,
    MyActivityGroups,
    MyActivityRead,
)
from app.schemas.common import Page
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/activities", tags=["activities"])

DbSession = Annotated[Session, Depends(get_db)]


def _to_read(service: ActivityService, activity: object) -> ActivityRead:
    data = ActivityRead.model_validate(activity)
    data.participant_count = service.participant_count(activity.id)  # type: ignore[attr-defined]
    data.waitlist_count = service.waitlist_count(activity.id)  # type: ignore[attr-defined]
    return data


@router.get("", response_model=Page[ActivityRead])
def list_activities(
    db: DbSession,
    category: Annotated[ActivityCategory | None, Query()] = None,
    sport: Annotated[str | None, Query(alias="sport", max_length=40)] = None,
    sport_slug: Annotated[str | None, Query(max_length=40)] = None,
    sport_category: Annotated[SportCategory | None, Query()] = None,
    type: Annotated[str | None, Query(alias="type", max_length=40)] = None,
    skill_level: Annotated[SkillLevel | None, Query()] = None,
    level: Annotated[SkillLevel | None, Query(alias="level")] = None,
    city: Annotated[str | None, Query(max_length=120)] = None,
    venue_id: Annotated[uuid.UUID | None, Query()] = None,
    host_id: Annotated[uuid.UUID | None, Query()] = None,
    starts_after: Annotated[datetime | None, Query()] = None,
    starts_before: Annotated[datetime | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=160)] = None,
    q: Annotated[str | None, Query(max_length=160)] = None,
    include_cancelled: bool = False,
    upcoming: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ActivityRead]:
    """List/filter/search activities with pagination.

    ``?upcoming=true`` restricts to activities that have not started yet
    (``starts_at >= now``) and, via the repository ordering, returns the
    soonest-first - the home widgets rely on this so already-past events
    never lead the rails.
    """
    service = ActivityService(db)
    rows, total = service.list_activities(
        category=str(category) if category else None,
        sport_slug=sport_slug or sport,
        sport_category=str(sport_category) if sport_category else None,
        activity_type=type,
        skill_level=str(skill_level or level) if (skill_level or level) else None,
        city=city,
        venue_id=venue_id,
        host_id=host_id,
        starts_after=starts_after or (datetime.now(UTC) if upcoming else None),
        starts_before=starts_before,
        search=search or q,
        include_cancelled=include_cancelled,
        limit=limit,
        offset=offset,
    )
    return Page[ActivityRead](
        items=[_to_read(service, a) for a in rows], total=total, limit=limit, offset=offset
    )


def _to_mine_read(service: ActivityService, entry: object) -> MyActivityRead:
    """Map a service ``MyActivityEntry`` onto the API schema."""
    activity = entry.activity  # type: ignore[attr-defined]
    data = MyActivityRead.model_validate(activity)
    data.participant_count = service.participant_count(activity.id)
    data.waitlist_count = service.waitlist_count(activity.id)
    data.state = entry.state  # type: ignore[attr-defined]
    data.participation_status = entry.participation_status  # type: ignore[attr-defined]
    data.is_host = entry.is_host  # type: ignore[attr-defined]
    data.attendance = entry.attendance  # type: ignore[attr-defined]
    data.sport_label = entry.sport_label  # type: ignore[attr-defined]
    data.sport_label_en = entry.sport_label_en  # type: ignore[attr-defined]
    data.venue_label = entry.venue_label  # type: ignore[attr-defined]
    data.court_label = entry.court_label  # type: ignore[attr-defined]
    return data


@router.get("/mine", response_model=MyActivitiesRead)
def list_my_activities(
    current_user: CurrentUser,
    db: DbSession,
    status: Annotated[str | None, Query(pattern="^(upcoming|waitlisted|past|hosting)$")] = None,
    sport: Annotated[str | None, Query(max_length=40)] = None,
    active_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MyActivitiesRead:
    """The authenticated caller's own activities ("Aktivitas Saya").

    Real, caller-scoped history: derived from the caller's persisted
    ``ActivityParticipant`` rows (joined/waitlisted/host) plus their persisted
    check-ins for attendance, split into four real states - ``upcoming``,
    ``waitlisted``, ``past`` (attended/no_show/cancelled) and ``hosting``.

    Each item carries the sport slug + label, the venue/court label, the start
    time and the caller's status/attendance. Optional ``?status=``,
    ``?sport=`` and ``?active_only=`` filters and ``limit``/``offset`` paging;
    ``items`` honours the filters while ``groups`` always exposes the full
    (sport-filtered) partition. ``?active_only=true`` drops already-finished
    items so a caller with no upcoming/ongoing registration gets an empty page
    (home "Aktivitas Saya" rails use it to avoid leading with stale history).
    Never returns another user's rows. Must be declared before ``/{activity_id}``
    so the literal path wins.
    """
    service = ActivityService(db)
    rows, total, groups = service.list_mine(
        current_user.id,
        status=status,
        sport=sport,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return MyActivitiesRead(
        items=[_to_mine_read(service, e) for e in rows],
        total=total,
        limit=limit,
        offset=offset,
        groups=MyActivityGroups(
            upcoming=[_to_mine_read(service, e) for e in groups.get("upcoming", [])],
            waitlisted=[_to_mine_read(service, e) for e in groups.get("waitlisted", [])],
            past=[_to_mine_read(service, e) for e in groups.get("past", [])],
            hosting=[_to_mine_read(service, e) for e in groups.get("hosting", [])],
        ),
    )


@router.post("", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate, current_user: CurrentUser, db: DbSession
) -> ActivityRead:
    """Create a sport-specific activity; the caller becomes its host."""
    service = ActivityService(db)
    activity = service.create(current_user.id, payload.model_dump())
    return _to_read(service, activity)


@router.get("/{activity_id}", response_model=ActivityRead)
def get_activity(activity_id: uuid.UUID, db: DbSession) -> ActivityRead:
    service = ActivityService(db)
    return _to_read(service, service.get(activity_id))


@router.patch("/{activity_id}", response_model=ActivityRead)
def update_activity(
    activity_id: uuid.UUID,
    payload: ActivityUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ActivityRead:
    """Host/owner-only partial update."""
    service = ActivityService(db)
    activity = service.update(
        activity_id, current_user.id, payload.model_dump(exclude_unset=True)
    )
    return _to_read(service, activity)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> None:
    """Host/owner-only delete."""
    ActivityService(db).delete(activity_id, current_user.id)


@router.post("/{activity_id}/join", response_model=ActivityParticipantRead)
def join_activity(
    activity_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> ActivityParticipantRead:
    """Join an activity; a full activity waitlists the joiner.

    The host is notified of the new participant either way.
    """
    service = ActivityService(db)
    activity = service.get(activity_id)
    participant = service.join(activity_id, current_user.id)
    if activity.host_id != current_user.id:
        verb = "waitlisted for" if participant.status == "waitlisted" else "joined"
        NotificationService(db).notify(
            activity.host_id,
            type=NotificationType.JOIN_REQUEST,
            title=f"New participant {verb} your activity",
            body=f"A participant {verb} {activity.title!r}.",
            data={"activity_id": str(activity_id), "user_id": str(current_user.id)},
        )
    return ActivityParticipantRead.model_validate(participant)


@router.post("/{activity_id}/cancel", response_model=ActivityRead)
def cancel_activity(
    activity_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> ActivityRead:
    """Cancel an activity (host only); every participant is notified."""
    service = ActivityService(db)
    activity = service.get(activity_id)
    service.cancel(activity_id, current_user.id)
    service.refresh(activity)
    participants = service.list_participants(activity_id)
    NotificationService(db).notify_many(
        [p.user_id for p in participants if p.user_id != current_user.id],
        type=NotificationType.ACTIVITY_INVITE,
        title="Activity cancelled",
        body=f"The activity {activity.title!r} was cancelled.",
        data={"activity_id": str(activity_id)},
    )
    return _to_read(service, activity)


@router.post("/{activity_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_activity(
    activity_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> None:
    """Leave an activity; a freed slot promotes the next waitlisted participant."""
    ActivityService(db).leave(activity_id, current_user.id)


@router.get("/{activity_id}/participants", response_model=list[ActivityParticipantRead])
def list_participants(
    activity_id: uuid.UUID, db: DbSession
) -> list[ActivityParticipantRead]:
    rows = ActivityService(db).list_participants(activity_id)
    return [ActivityParticipantRead.model_validate(p) for p in rows]
