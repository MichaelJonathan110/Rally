"""Media upload service: validate, persist and address user-uploaded files.

Files are written under ``settings.MEDIA_ROOT`` and served read-only by the
``/media`` StaticFiles mount. The public URL returned to clients is a *relative*
path (``/media/<subdir>/<uuid>.<ext>``) so the same value works in dev and behind
a proxy without rewriting.

Ownership is tracked in a small JSON registry (``.owners.json``) living beside
the media files: it maps the public relative URL to the uploader's user id so
``DELETE`` can enforce that a user only removes their own uploads.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import DomainError, ValidationError

#: Purposes map to a sub-directory; anything else is rejected.
ALLOWED_PURPOSES: frozenset[str] = frozenset({"avatar", "activity", "venue", "review"})

#: Image extensions we accept, mapped to the canonical content types.
ALLOWED_IMAGE_TYPES: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
}

#: Magic-byte prefixes used to confirm the bytes really are an image.
_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)

_READ_CHUNK = 64 * 1024


class FileTooLargeError(DomainError):
    """The upload exceeds ``MAX_UPLOAD_MB`` -> HTTP 413."""

    status_code = 413
    default_detail = "Uploaded file is too large"


class MediaService:
    """Validate and store uploads; enforce per-user ownership for deletes."""

    def __init__(self, media_root: str | Path | None = None) -> None:
        self.media_root = Path(media_root or settings.MEDIA_ROOT).resolve()
        self._registry_path = self.media_root / ".owners.json"

    # -- helpers -------------------------------------------------------------
    @property
    def max_bytes(self) -> int:
        return settings.MAX_UPLOAD_MB * 1024 * 1024

    def ensure_root(self) -> None:
        """Create the media root (idempotent)."""
        self.media_root.mkdir(parents=True, exist_ok=True)

    def _load_registry(self) -> dict[str, str]:
        if not self._registry_path.exists():
            return {}
        try:
            data = json.loads(self._registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_registry(self, registry: dict[str, str]) -> None:
        self.ensure_root()
        self._registry_path.write_text(json.dumps(registry), encoding="utf-8")

    @staticmethod
    def _sanitize_extension(filename: str | None) -> str:
        """Return a lower-cased, whitelisted extension from ``filename``."""
        raw = (filename or "").strip().replace("\\", "/").split("/")[-1]
        ext = raw.rsplit(".", 1)[-1].lower() if "." in raw else ""
        if ext not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(
                "Unsupported file type; allowed: " + ", ".join(sorted(ALLOWED_IMAGE_TYPES))
            )
        return ext

    @staticmethod
    def _looks_like_image(head: bytes, content_type: str | None) -> bool:
        for prefix, _ in _MAGIC:
            if head.startswith(prefix):
                return True
        # WEBP: RIFF....WEBP
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            return True
        # Fall back to the declared content type only if the caller sent one.
        return bool(content_type and content_type.startswith("image/"))

    # -- public API ----------------------------------------------------------
    def save_upload(self, file: UploadFile, subdir: str, user_id: uuid.UUID) -> dict[str, object]:
        """Validate ``file`` and persist it under ``<media_root>/<subdir>``.

        Returns a metadata dict: ``url``, ``filename``, ``size``, ``content_type``.
        """
        if subdir not in ALLOWED_PURPOSES:
            raise ValidationError(
                "Invalid purpose; allowed: " + ", ".join(sorted(ALLOWED_PURPOSES))
            )

        ext = self._sanitize_extension(file.filename)
        content_type = file.content_type or ALLOWED_IMAGE_TYPES[ext]

        dest_dir = self.media_root / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"{uuid.uuid4().hex}.{ext}"
        dest_path = dest_dir / stored_name

        size = 0
        head = b""
        source = file.file
        try:
            source.seek(0)
        except (OSError, ValueError):
            pass

        with dest_path.open("wb") as out:
            while True:
                chunk = source.read(_READ_CHUNK)
                if not chunk:
                    break
                if not head:
                    head = chunk[:16]
                size += len(chunk)
                if size > self.max_bytes:
                    out.close()
                    dest_path.unlink(missing_ok=True)
                    raise FileTooLargeError(
                        f"File exceeds the {settings.MAX_UPLOAD_MB} MB limit"
                    )
                out.write(chunk)

        if size == 0:
            dest_path.unlink(missing_ok=True)
            raise ValidationError("Uploaded file is empty")

        if not self._looks_like_image(head, content_type):
            dest_path.unlink(missing_ok=True)
            raise ValidationError("File does not look like a valid image")

        rel_url = f"{settings.MEDIA_URL_PREFIX}/{subdir}/{stored_name}"
        registry = self._load_registry()
        registry[rel_url] = str(user_id)
        self._save_registry(registry)

        return {
            "url": rel_url,
            "filename": stored_name,
            "size": size,
            "content_type": content_type,
        }

    def delete_upload(self, subdir: str, name: str, user_id: uuid.UUID) -> None:
        """Delete ``name`` from ``subdir`` if it belongs to ``user_id``.

        Raises ``ValidationError`` for a malformed path, ``NotFoundError`` when
        the file is unknown and ``PermissionDeniedError`` when the caller does
        not own it.
        """
        from app.core.exceptions import NotFoundError, PermissionDeniedError

        if subdir not in ALLOWED_PURPOSES:
            raise ValidationError("Invalid purpose")
        safe_name = Path(name).name
        if not safe_name or safe_name != name or safe_name.startswith("."):
            raise ValidationError("Invalid file name")

        rel_url = f"{settings.MEDIA_URL_PREFIX}/{subdir}/{safe_name}"
        target = (self.media_root / subdir / safe_name).resolve()
        # Defend against path traversal: target must stay under the media root.
        if self.media_root not in target.parents:
            raise ValidationError("Invalid file path")
        if not target.is_file():
            raise NotFoundError("Media file not found")

        registry = self._load_registry()
        owner = registry.get(rel_url)
        if owner is not None and owner != str(user_id):
            raise PermissionDeniedError("You can only delete your own uploads")

        target.unlink(missing_ok=True)
        if rel_url in registry:
            registry.pop(rel_url, None)
            self._save_registry(registry)
