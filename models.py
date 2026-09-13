"""Data models for Telegram posts and media items with SQLite and export support."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class MediaItem:
    message_id: int
    media_type: str
    file_name: str
    file_path: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    duration_seconds: Optional[float] = None
    download_status: str = "downloaded"  # "downloaded", "failed", "skipped", "skipped_duration"
    id: Optional[int] = None

    def __post_init__(self):
        if self.file_size is not None and not isinstance(self.file_size, int):
            try:
                self.file_size = int(self.file_size)
            except (ValueError, TypeError):
                self.file_size = None
        if self.duration_seconds is not None and not isinstance(self.duration_seconds, (int, float)):
            try:
                self.duration_seconds = float(self.duration_seconds)
            except (ValueError, TypeError):
                self.duration_seconds = None

    def to_db_tuple(self) -> tuple:
        return (
            self.message_id,
            self.media_type,
            self.file_name,
            self.file_path,
            self.mime_type,
            self.file_size,
            self.duration_seconds,
            self.download_status,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "media_type": self.media_type,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "duration_seconds": self.duration_seconds,
            "download_status": self.download_status,
        }


@dataclass
class Post:
    message_id: int
    channel: str
    date: str
    text: str
    views: Optional[int] = None
    forwards: Optional[int] = None
    replies: Optional[int] = None
    url: Optional[str] = None
    has_media: int = 0  # 1 or 0
    media_type: Optional[str] = None
    media_path: Optional[str] = None
    media_status: Optional[str] = "none"  # "none", "downloaded", "skipped", "skipped_duration", "failed"
    duration_seconds: Optional[float] = None
    grouped_id: Optional[int] = None
    created_at: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if isinstance(self.has_media, bool):
            self.has_media = 1 if self.has_media else 0
        if self.views is not None and not isinstance(self.views, int):
            try:
                self.views = int(self.views)
            except (ValueError, TypeError):
                self.views = None
        if self.forwards is not None and not isinstance(self.forwards, int):
            try:
                self.forwards = int(self.forwards)
            except (ValueError, TypeError):
                self.forwards = None
        if self.replies is not None and not isinstance(self.replies, int):
            try:
                self.replies = int(self.replies)
            except (ValueError, TypeError):
                self.replies = None
        if self.duration_seconds is not None and not isinstance(self.duration_seconds, (int, float)):
            try:
                self.duration_seconds = float(self.duration_seconds)
            except (ValueError, TypeError):
                self.duration_seconds = None

    def to_db_tuple(self) -> tuple:
        return (
            self.message_id,
            self.channel,
            self.date,
            self.text,
            self.views,
            self.forwards,
            self.replies,
            self.url,
            self.has_media,
            self.media_type,
            self.media_path,
            self.media_status,
            self.duration_seconds,
            self.grouped_id,
            self.created_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "channel": self.channel,
            "date": self.date,
            "text": self.text,
            "views": self.views,
            "forwards": self.forwards,
            "replies": self.replies,
            "url": self.url,
            "has_media": bool(self.has_media),
            "media_type": self.media_type,
            "media_path": self.media_path,
            "media_status": self.media_status,
            "duration_seconds": self.duration_seconds,
            "grouped_id": self.grouped_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Post":
        return cls(
            message_id=data.get("message_id", 0),
            channel=data.get("channel", ""),
            date=data.get("date", ""),
            text=data.get("text", ""),
            views=data.get("views"),
            forwards=data.get("forwards"),
            replies=data.get("replies"),
            url=data.get("url"),
            has_media=1 if data.get("has_media") else 0,
            media_type=data.get("media_type"),
            media_path=data.get("media_path") or data.get("media_file"),
            media_status=data.get("media_status", "none"),
            duration_seconds=data.get("duration_seconds"),
            grouped_id=data.get("grouped_id"),
            created_at=data.get("created_at"),
            id=data.get("id"),
        )

    def to_csv_row(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "channel": self.channel,
            "date": self.date,
            "text": self.text,
            "views": self.views if self.views is not None else "",
            "forwards": self.forwards if self.forwards is not None else "",
            "replies": self.replies if self.replies is not None else "",
            "url": self.url or "",
            "has_media": self.has_media,
            "media_type": self.media_type or "",
            "media_path": self.media_path or "",
            "media_status": self.media_status or "",
            "duration_seconds": self.duration_seconds if self.duration_seconds is not None else "",
            "grouped_id": self.grouped_id if self.grouped_id is not None else "",
            "created_at": self.created_at or "",
        }


CSV_FIELDNAMES = [
    "message_id",
    "channel",
    "date",
    "text",
    "views",
    "forwards",
    "replies",
    "url",
    "has_media",
    "media_type",
    "media_path",
    "media_status",
    "duration_seconds",
    "grouped_id",
    "created_at",
]
