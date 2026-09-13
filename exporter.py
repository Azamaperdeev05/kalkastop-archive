"""Telegram Channel Exporter core logic: SQLite persistence, video duration filtering, and media downloads."""

import os
import mimetypes
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Set, List, Optional, Tuple
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.tl.types import (
    Message,
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaPoll,
    MessageMediaWebPage,
    MessageMediaContact,
    MessageMediaGeo,
    DocumentAttributeFilename,
    DocumentAttributeAudio,
    DocumentAttributeVideo,
    DocumentAttributeAnimated,
    DocumentAttributeSticker,
)
from telethon.errors import FloodWaitError, RPCError

from models import Post, MediaItem
from database import Database
from progress import ExporterProgressUI

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent illegal filesystem characters."""
    keepchars = ("-", "_", ".", " ")
    cleaned = "".join(c for c in filename if c.isalnum() or c in keepchars).rstrip()
    return cleaned or "file"


class ChannelExporter:
    """Handles exporting channel posts and filtered media into a local SQLite database."""

    def __init__(
        self,
        client: TelegramClient,
        entity: Any,
        channel_title: str,
        channel_username: str,
        export_dir: Path,
        db: Database,
        download_media: bool = True,
        max_video_duration: float = 120.0,
        progress_ui: Optional[ExporterProgressUI] = None,
    ):
        self.client = client
        self.entity = entity
        self.channel_title = channel_title
        self.channel_username = channel_username
        self.export_dir = export_dir
        self.db = db
        self.download_media = download_media
        self.max_video_duration = max_video_duration
        self.progress_ui = progress_ui

        # Subdirectories for categorized media
        self.media_dirs = {
            "images": self.export_dir / "media" / "images",
            "videos": self.export_dir / "media" / "videos",
            "documents": self.export_dir / "media" / "documents",
            "audio": self.export_dir / "media" / "audio",
            "voice": self.export_dir / "media" / "voice",
            "animations": self.export_dir / "media" / "animations",
            "other": self.export_dir / "media" / "other",
        }

        # State tracking loaded from SQLite
        self.processed_ids: Set[int] = set()
        self.last_processed_id: int = 0

        # Live counters
        self.posts_processed: int = 0
        self.posts_saved: int = 0
        self.media_found: int = 0
        self.media_downloaded: int = 0
        self.photos_downloaded: int = 0
        self.short_videos_downloaded: int = 0
        self.long_videos_skipped: int = 0
        self.audio_skipped: int = 0
        self.documents_skipped: int = 0
        self.media_failed: int = 0

        self.stop_requested: bool = False

    def init_filesystem(self):
        """Create export folder and media subdirectories."""
        self.export_dir.mkdir(parents=True, exist_ok=True)
        for d in self.media_dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    def load_state_from_db(self):
        """Load existing processed posts and stats from SQLite database to resume."""
        self.processed_ids = self.db.get_processed_ids(self.channel_username)
        self.last_processed_id = self.db.get_last_processed_id(self.channel_username)

        stats = self.db.get_summary_stats(self.channel_username)
        self.posts_saved = stats["total_posts"]
        self.posts_processed = len(self.processed_ids)
        self.media_found = stats["posts_with_media"]
        self.media_downloaded = stats["media_downloaded"]
        self.photos_downloaded = stats["photos_downloaded"]
        self.short_videos_downloaded = stats["short_videos_downloaded"]
        self.long_videos_skipped = stats["long_videos_skipped"]
        self.audio_skipped = stats["audio_skipped"]
        self.documents_skipped = stats["documents_skipped"]
        self.media_failed = stats["download_failures"]

        logger.info(
            f"Loaded state from SQLite: {self.posts_saved} posts, "
            f"{self.photos_downloaded} photos, {self.short_videos_downloaded} short videos, "
            f"{self.long_videos_skipped} videos skipped, {self.audio_skipped} audio skipped, "
            f"{self.documents_skipped} docs skipped, last ID: {self.last_processed_id}"
        )

    def detect_media_type_and_category(
        self, message: Message
    ) -> Tuple[Optional[str], str, Optional[str], Optional[str], Optional[float]]:
        """
        Detects media type, target category folder, default extension, MIME type, and duration.
        Returns: (media_type, category, ext, mime_type, duration_seconds)
        """
        if not message.media:
            return None, "", None, None, None

        if isinstance(message.media, MessageMediaPhoto):
            return "photo", "images", "jpg", "image/jpeg", None

        if isinstance(message.media, MessageMediaPoll):
            return "poll", "", None, None, None

        if isinstance(message.media, MessageMediaWebPage):
            return "web_page", "", None, None, None

        if isinstance(message.media, MessageMediaContact):
            return "contact", "", None, None, None

        if isinstance(message.media, MessageMediaGeo):
            return "geo", "", None, None, None

        if isinstance(message.media, MessageMediaDocument):
            doc = message.media.document
            if not doc:
                return "document", "documents", "bin", "application/octet-stream", None

            mime = getattr(doc, "mime_type", "") or ""

            # Inspect document attributes
            is_animated = False
            is_voice = False
            is_audio = False
            is_video = False
            is_sticker = False
            file_name_attr = None
            duration = None

            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeAnimated):
                    is_animated = True
                elif isinstance(attr, DocumentAttributeAudio):
                    duration = getattr(attr, "duration", None)
                    if getattr(attr, "voice", False):
                        is_voice = True
                    else:
                        is_audio = True
                elif isinstance(attr, DocumentAttributeVideo):
                    duration = getattr(attr, "duration", None)
                    is_video = True
                elif isinstance(attr, DocumentAttributeSticker):
                    is_sticker = True
                elif isinstance(attr, DocumentAttributeFilename):
                    file_name_attr = attr.file_name

            duration_val = float(duration) if duration is not None else None

            # Classify
            if is_animated or mime == "image/gif":
                return "animation", "animations", "mp4", mime or "video/mp4", duration_val

            if is_voice:
                return "voice", "voice", "ogg", mime or "audio/ogg", duration_val

            if is_audio or mime.startswith("audio/"):
                return "audio", "audio", "mp3", mime or "audio/mpeg", duration_val

            if is_video or mime.startswith("video/"):
                return "video", "videos", "mp4", mime or "video/mp4", duration_val

            if is_sticker:
                return "sticker", "other", "webp", mime or "image/webp", duration_val

            if mime.startswith("image/"):
                ext = mime.split("/")[-1].lower() if "/" in mime else "jpg"
                return "photo", "images", ext, mime, None

            # Default to document
            ext = None
            if file_name_attr and "." in file_name_attr:
                ext = file_name_attr.rsplit(".", 1)[-1].lower()
            elif "/" in mime:
                ext = mime.split("/")[-1].lower()
            return "document", "documents", ext or "bin", mime or "application/octet-stream", duration_val

        return "other", "other", "bin", "application/octet-stream", None

    def get_target_file_info(
        self,
        message: Message,
        category: str,
        ext: Optional[str],
        mime_type: Optional[str],
    ) -> Tuple[Path, str, str]:
        """
        Determines target file path and relative path incorporating message ID.
        Returns: (full_disk_path, relative_path, file_name)
        """
        dest_dir = self.media_dirs.get(category, self.media_dirs["other"])

        original_filename = None
        if isinstance(message.media, MessageMediaDocument) and message.media.document:
            for attr in message.media.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    original_filename = attr.file_name
                    break

        if original_filename:
            clean_name = sanitize_filename(original_filename)
            file_name = f"{message.id}_{clean_name}"
        else:
            file_name = f"{message.id}.{ext or 'bin'}"

        full_path = dest_dir / file_name
        rel_path = f"media/{category}/{file_name}"
        return full_path, rel_path, file_name

    async def download_media_file(
        self,
        message: Message,
        category: str,
        ext: Optional[str],
        mime_type: Optional[str],
    ) -> Tuple[Optional[str], Optional[str], Optional[int], str]:
        """
        Downloads media with size verification and FloodWait handling.
        Returns: (relative_file_path, file_name, file_size, status)
        """
        if not self.download_media or not category:
            return None, None, None, "skipped"

        target_file, rel_path, file_name = self.get_target_file_info(message, category, ext, mime_type)

        # Resume check: If file already exists and size matches expected size, skip download
        expected_size = getattr(getattr(message, "file", None), "size", None)
        if target_file.exists() and target_file.stat().st_size > 0:
            actual_size = target_file.stat().st_size
            if expected_size is None or actual_size == expected_size:
                return rel_path, file_name, actual_size, "downloaded"

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.progress_ui:
                    self.progress_ui.update(
                        status_message=f"Downloading {category} for msg {message.id}..."
                    )

                path = await self.client.download_media(message, file=str(target_file))
                if path and Path(path).exists() and Path(path).stat().st_size > 0:
                    file_size = Path(path).stat().st_size
                    return rel_path, file_name, file_size, "downloaded"
                else:
                    return None, file_name, None, "failed"

            except FloodWaitError as e:
                wait_time = e.seconds + 1
                logger.warning(f"FloodWaitError: sleeping {wait_time}s")
                if self.progress_ui:
                    self.progress_ui.update(status_message=f"FloodWait: sleeping {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error downloading media for msg {message.id} (attempt {attempt + 1}): {e}")
                await asyncio.sleep(1)

        return None, file_name, None, "failed"

    def parse_post(
        self,
        message: Message,
        media_type: Optional[str],
        media_path: Optional[str],
        media_status: str,
        duration: Optional[float] = None,
    ) -> Post:
        """Construct Post model matching the SQLite schema."""
        text = str(message.text or message.raw_text or "")
        date_str = message.date.isoformat() if message.date else ""

        url = None
        if self.channel_username:
            url = f"https://t.me/{self.channel_username}/{message.id}"

        replies_count = None
        if message.replies:
            replies_count = getattr(message.replies, "replies", None)

        has_media_flag = 1 if bool(message.media) else 0

        return Post(
            message_id=message.id,
            channel=self.channel_username,
            date=date_str,
            text=text,
            views=message.views,
            forwards=message.forwards,
            replies=replies_count,
            url=url,
            has_media=has_media_flag,
            media_type=media_type,
            media_path=media_path,
            media_status=media_status,
            duration_seconds=duration,
            grouped_id=message.grouped_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    async def run(self):
        """Execute chronological export from oldest to newest post with SQLite storage, duration filter, and media downloads."""
        self.init_filesystem()
        self.load_state_from_db()

        if self.progress_ui:
            self.progress_ui.update(
                posts_processed=self.posts_processed,
                posts_saved=self.posts_saved,
                media_found=self.media_found,
                media_downloaded=self.media_downloaded,
                photos_downloaded=self.photos_downloaded,
                short_videos_downloaded=self.short_videos_downloaded,
                long_videos_skipped=self.long_videos_skipped,
                audio_skipped=self.audio_skipped,
                documents_skipped=self.documents_skipped,
                media_failed=self.media_failed,
                current_message_id=self.last_processed_id,
                status_message="Connected to SQLite. Starting message extraction...",
            )

        min_id = 0
        consecutive_errors = 0

        while not self.stop_requested:
            try:
                async for message in self.client.iter_messages(
                    self.entity,
                    reverse=True,
                    min_id=min_id,
                ):
                    if self.stop_requested:
                        break

                    if not message or not getattr(message, "id", None):
                        continue

                    current_id = message.id
                    self.posts_processed += 1

                    # Skip if already processed and complete in SQLite
                    if current_id in self.processed_ids and self.db.is_message_complete(current_id):
                        if self.progress_ui:
                            self.progress_ui.update(
                                posts_processed=self.posts_processed,
                                current_message_id=current_id,
                                status_message=f"Verified msg {current_id} in SQLite",
                            )
                        continue

                    try:
                        (
                            media_type,
                            category,
                            ext,
                            mime_type,
                            duration,
                        ) = self.detect_media_type_and_category(message)
                        has_media = bool(message.media)

                        media_path = None
                        media_status = "none"
                        media_items: List[MediaItem] = []

                        if has_media:
                            self.media_found += 1
                            is_video = category == "videos" or media_type in ("video", "round_video")
                            is_audio = category in ("audio", "voice") or media_type in ("audio", "voice")
                            is_document = category == "documents" or media_type == "document"
                            is_photo = category == "images" or media_type == "photo"

                            target_file, rel_path, file_name = self.get_target_file_info(
                                message, category, ext, mime_type
                            )
                            expected_size = getattr(getattr(message, "file", None), "size", None)

                            # 1. AUDIO / VOICE: DO NOT DOWNLOAD, save metadata
                            if is_audio:
                                media_status = "skipped_audio"
                                media_path = None
                                self.audio_skipped += 1
                                media_items.append(
                                    MediaItem(
                                        message_id=current_id,
                                        media_type=media_type or "audio",
                                        file_name=file_name,
                                        file_path="",
                                        mime_type=mime_type,
                                        file_size=expected_size,
                                        duration_seconds=duration,
                                        download_status="skipped_audio",
                                    )
                                )
                                logger.info(f"Skipping audio for msg {current_id}")

                            # 2. DOCUMENTS: DO NOT DOWNLOAD, save metadata
                            elif is_document:
                                media_status = "skipped_document"
                                media_path = None
                                self.documents_skipped += 1
                                media_items.append(
                                    MediaItem(
                                        message_id=current_id,
                                        media_type=media_type or "document",
                                        file_name=file_name,
                                        file_path="",
                                        mime_type=mime_type,
                                        file_size=expected_size,
                                        duration_seconds=duration,
                                        download_status="skipped_document",
                                    )
                                )
                                logger.info(f"Skipping document for msg {current_id}")

                            # 3. VIDEOS: Inspect duration
                            elif is_video:
                                if duration is not None and duration > self.max_video_duration:
                                    # Video > 120s -> SKIP
                                    media_status = "skipped_duration"
                                    media_path = None
                                    self.long_videos_skipped += 1
                                    media_items.append(
                                        MediaItem(
                                            message_id=current_id,
                                            media_type=media_type or "video",
                                            file_name=file_name,
                                            file_path="",
                                            mime_type=mime_type,
                                            file_size=expected_size,
                                            duration_seconds=duration,
                                            download_status="skipped_duration",
                                        )
                                    )
                                    logger.info(
                                        f"Skipping video for msg {current_id}: duration {duration:.1f}s > {self.max_video_duration}s"
                                    )
                                elif self.download_media:
                                    # Video <= 120s -> DOWNLOAD
                                    media_path, file_name, file_size, media_status = await self.download_media_file(
                                        message, category, ext, mime_type
                                    )
                                    if media_status == "downloaded":
                                        self.short_videos_downloaded += 1
                                        self.media_downloaded += 1
                                    elif media_status == "failed":
                                        self.media_failed += 1
                                    media_items.append(
                                        MediaItem(
                                            message_id=current_id,
                                            media_type=media_type or "video",
                                            file_name=file_name,
                                            file_path=media_path or "",
                                            mime_type=mime_type,
                                            file_size=file_size,
                                            duration_seconds=duration,
                                            download_status=media_status,
                                        )
                                    )
                                else:
                                    media_status = "skipped"

                            # 4. PHOTOS: DOWNLOAD
                            elif is_photo:
                                if self.download_media:
                                    media_path, file_name, file_size, media_status = await self.download_media_file(
                                        message, category, ext, mime_type
                                    )
                                    if media_status == "downloaded":
                                        self.photos_downloaded += 1
                                        self.media_downloaded += 1
                                    elif media_status == "failed":
                                        self.media_failed += 1
                                    media_items.append(
                                        MediaItem(
                                            message_id=current_id,
                                            media_type=media_type or "photo",
                                            file_name=file_name,
                                            file_path=media_path or "",
                                            mime_type=mime_type,
                                            file_size=file_size,
                                            duration_seconds=duration,
                                            download_status=media_status,
                                        )
                                    )
                                else:
                                    media_status = "skipped"

                            # 5. ALL OTHER MEDIA: SKIP download, save metadata
                            else:
                                media_status = "skipped"
                                media_items.append(
                                    MediaItem(
                                        message_id=current_id,
                                        media_type=media_type or "other",
                                        file_name=file_name,
                                        file_path="",
                                        mime_type=mime_type,
                                        file_size=expected_size,
                                        duration_seconds=duration,
                                        download_status="skipped",
                                    )
                                )

                        # Parse Post model
                        post = self.parse_post(message, media_type, media_path, media_status, duration)

                        # Save to SQLite in atomic transaction
                        self.db.save_post_and_media(post, media_items)

                        if current_id not in self.processed_ids:
                            self.posts_saved += 1
                            self.processed_ids.add(current_id)

                        self.last_processed_id = max(self.last_processed_id, current_id)
                        consecutive_errors = 0

                        # Update progress UI
                        if self.progress_ui:
                            self.progress_ui.update(
                                posts_processed=self.posts_processed,
                                posts_saved=self.posts_saved,
                                media_found=self.media_found,
                                media_downloaded=self.media_downloaded,
                                photos_downloaded=self.photos_downloaded,
                                short_videos_downloaded=self.short_videos_downloaded,
                                long_videos_skipped=self.long_videos_skipped,
                                audio_skipped=self.audio_skipped,
                                documents_skipped=self.documents_skipped,
                                media_failed=self.media_failed,
                                current_message_id=current_id,
                                status_message=f"Saved msg {current_id} ({media_status})",
                            )

                    except Exception as msg_err:
                        self.media_failed += 1
                        logger.error(f"Failed processing message {current_id}: {msg_err}")
                        if self.progress_ui:
                            self.progress_ui.update(
                                media_failed=self.media_failed,
                                status_message=f"Error on msg {current_id}",
                            )

                # Completed full iteration
                break

            except FloodWaitError as e:
                wait_time = e.seconds + 1
                logger.warning(f"FloodWait: waiting {wait_time}s")
                if self.progress_ui:
                    self.progress_ui.update(status_message=f"FloodWait: waiting {wait_time}s...")
                await asyncio.sleep(wait_time)

            except (RPCError, ConnectionError, OSError) as net_err:
                consecutive_errors += 1
                logger.warning(f"Network / RPC error: {net_err}. Retry #{consecutive_errors}")
                if consecutive_errors > 5:
                    logger.error("Too many consecutive errors, aborting.")
                    break
                await asyncio.sleep(2 * consecutive_errors)

            except Exception as unk_err:
                logger.error(f"Unexpected error in message loop: {unk_err}")
                break
