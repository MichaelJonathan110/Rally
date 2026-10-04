"""API v1 package: aggregates all routers under a single APIRouter."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    activities,
    admin,
    catalog,
    auth,
    bookings,
    chat,
    checkin,
    clubs,
    follows,
    health,
    matchmaking,
    matches,
    media,
    notifications,
    progress,
    reports,
    sports,
    tournaments,
    users,
    venue_map,
    venues,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(activities.router)
api_router.include_router(catalog.router)
api_router.include_router(sports.router)
api_router.include_router(venue_map.router)
api_router.include_router(venues.router)
api_router.include_router(clubs.router)
api_router.include_router(follows.router)
api_router.include_router(bookings.router)
api_router.include_router(chat.router)
api_router.include_router(checkin.router)
api_router.include_router(matches.router)
api_router.include_router(media.router)
api_router.include_router(notifications.router)
api_router.include_router(tournaments.router)
api_router.include_router(reports.router)
api_router.include_router(users.router)
api_router.include_router(progress.router)
api_router.include_router(matchmaking.router)
api_router.include_router(webhooks.router)

__all__ = ["api_router"]
