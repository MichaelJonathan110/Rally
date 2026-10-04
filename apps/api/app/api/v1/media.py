"""Media upload endpoints: multipart upload and owner-scoped delete.

Uploads are validated (extension, magic bytes, size) by
:class:`app.services.media_service.MediaService`, stored under
``settings.MEDIA_ROOT`` and served read-only via the ``/media`` StaticFiles
mount. These routes live under ``/api/v1/media`` for the *write* side; the
read side is the static mount (see ``app.main``).
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.services.media_service import ALLOWED_PURPOSES, MediaService

router = APIRouter(prefix="/media", tags=["media"])


class MediaUploadResponse(BaseModel):
    """Metadata for a freshly stored upload."""

    url: str
    filename: str
    size: int
    content_type: str


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    current_user: CurrentUser,
    file: Annotated[UploadFile, File(description="Image file to store")],
    purpose: Annotated[str, Form()] = "avatar",
) -> MediaUploadResponse:
    """Store an uploaded image and return its public URL.

    ``purpose`` selects the namespace (``avatar``, ``activity``, ``venue``,
    ``review``). Auth is required; the caller owns the stored file.
    """
    result = MediaService().save_upload(file, purpose, current_user.id)
    return MediaUploadResponse(**result)


@router.delete("/{subdir}/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(subdir: str, name: str, current_user: CurrentUser) -> None:
    """Delete one of the caller's own uploads (404 unknown, 403 not yours)."""
    MediaService().delete_upload(subdir, name, current_user.id)


__all__ = ["router", "ALLOWED_PURPOSES"]
