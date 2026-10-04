"""Reports, reviews, achievements and moderation business logic."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import (
    ModerationActionType,
    ReportStatus,
    ReviewTargetType,
    UserRole,
)
from app.models.social import (
    Achievement,
    ModerationAction,
    Report,
    Review,
    UserAchievement,
)
from app.models.user import User


class ReportService:
    """Reports filed by users and triaged by moderators/admins."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        reporter_id: uuid.UUID,
        *,
        target_type: object,
        target_id: uuid.UUID,
        reason: str,
        details: str | None = None,
    ) -> Report:
        report = Report(
            reporter_id=reporter_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            details=details,
            status=ReportStatus.OPEN,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def list_reports(
        self,
        *,
        status: ReportStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Report], int]:
        stmt = select(Report)
        if status is not None:
            stmt = stmt.where(Report.status == status)
        total = int(self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        rows = self.db.scalars(
            stmt.order_by(Report.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return list(rows), total

    def get(self, report_id: uuid.UUID) -> Report:
        report = self.db.get(Report, report_id)
        if report is None:
            raise NotFoundError("Report not found")
        return report

    def resolve(
        self,
        report_id: uuid.UUID,
        moderator_id: uuid.UUID,
        *,
        status: ReportStatus,
        note: str | None = None,
        action: ModerationActionType | None = None,
        target_user_id: uuid.UUID | None = None,
    ) -> Report:
        report = self.get(report_id)
        if report.status in (ReportStatus.RESOLVED, ReportStatus.DISMISSED):
            raise ConflictError("Report is already closed")
        report.status = status
        report.resolved_by_id = moderator_id
        report.resolved_at = datetime.now(UTC)
        if action is not None:
            self.db.add(
                ModerationAction(
                    report_id=report.id,
                    moderator_id=moderator_id,
                    target_user_id=target_user_id or report.target_id,
                    action=action,
                    reason=note,
                    metadata_json={"note": note} if note else None,
                )
            )
        self.db.commit()
        self.db.refresh(report)
        return report


class ModerationService:
    """Direct moderation actions (ban/unban) plus the action audit log."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_user(self, user_id: uuid.UUID) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def ban_user(
        self,
        target_user_id: uuid.UUID,
        moderator_id: uuid.UUID,
        *,
        reason: str | None = None,
        duration_hours: int | None = None,
    ) -> ModerationAction:
        user = self._get_user(target_user_id)
        if user.role == UserRole.ADMIN:
            raise ConflictError("Admins cannot be banned")
        user.is_active = False
        expires_at = (
            datetime.now(UTC) + timedelta(hours=duration_hours) if duration_hours else None
        )
        action = ModerationAction(
            moderator_id=moderator_id,
            target_user_id=target_user_id,
            action=ModerationActionType.BAN,
            reason=reason,
            expires_at=expires_at,
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def unban_user(
        self, target_user_id: uuid.UUID, moderator_id: uuid.UUID, *, reason: str | None = None
    ) -> ModerationAction:
        user = self._get_user(target_user_id)
        user.is_active = True
        action = ModerationAction(
            moderator_id=moderator_id,
            target_user_id=target_user_id,
            action=ModerationActionType.RESTORE_CONTENT,
            reason=reason or "Unbanned",
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def log_action(
        self,
        moderator_id: uuid.UUID,
        *,
        action: ModerationActionType,
        target_user_id: uuid.UUID | None = None,
        report_id: uuid.UUID | None = None,
        reason: str | None = None,
    ) -> ModerationAction:
        entry = ModerationAction(
            moderator_id=moderator_id,
            target_user_id=target_user_id,
            report_id=report_id,
            action=action,
            reason=reason,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_actions(
        self,
        *,
        target_user_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ModerationAction], int]:
        stmt = select(ModerationAction)
        if target_user_id is not None:
            stmt = stmt.where(ModerationAction.target_user_id == target_user_id)
        total = int(self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        rows = self.db.scalars(
            stmt.order_by(ModerationAction.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return list(rows), total


class ReviewService:
    """Venue (and generic target) reviews with an aggregate summary."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        author_id: uuid.UUID,
        *,
        target_type: ReviewTargetType,
        target_id: uuid.UUID,
        rating: int,
        body: str | None = None,
    ) -> Review:
        existing = self.db.scalar(
            select(Review).where(
                Review.author_id == author_id,
                Review.target_type == target_type,
                Review.target_id == target_id,
            )
        )
        if existing is not None:
            raise ConflictError("You have already reviewed this target")
        review = Review(
            author_id=author_id,
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            body=body,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def list_for_target(
        self, target_type: ReviewTargetType, target_id: uuid.UUID
    ) -> list[Review]:
        return list(
            self.db.scalars(
                select(Review)
                .where(Review.target_type == target_type, Review.target_id == target_id)
                .order_by(Review.created_at.desc())
            ).all()
        )

    def summary(self, target_type: ReviewTargetType, target_id: uuid.UUID) -> dict:
        reviews = self.list_for_target(target_type, target_id)
        count = len(reviews)
        avg = round(sum(r.rating for r in reviews) / count, 2) if count else 0.0
        return {"average_rating": avg, "review_count": count, "reviews": reviews}


class AchievementService:
    """Read-only achievement listings for a user."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def for_user(self, user_id: uuid.UUID) -> list[dict]:
        rows = self.db.execute(
            select(Achievement, UserAchievement.earned_at)
            .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
            .where(UserAchievement.user_id == user_id)
            .order_by(Achievement.points.desc())
        ).all()
        return [{"achievement": ach, "earned_at": earned_at} for ach, earned_at in rows]
