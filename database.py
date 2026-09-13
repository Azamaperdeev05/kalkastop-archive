"""SQLite Database Manager for Telegram Channel Exporter with duration and video filtering support."""

import sqlite3
import logging
from pathlib import Path
from typing import Set, List, Optional, Tuple, Dict, Any

from models import Post, MediaItem

logger = logging.getLogger(__name__)


class Database:
    """Handles SQLite persistence for posts and media."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Connect to SQLite and set pragmas."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
        )
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
            self.conn.execute("PRAGMA foreign_keys=ON;")
        self.init_schema()
        return self.conn

    def init_schema(self):
        """Create posts and media tables and indexes if not existing, and perform migrations."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER UNIQUE,
            channel TEXT,
            date TEXT,
            text TEXT,
            views INTEGER,
            forwards INTEGER,
            replies INTEGER,
            url TEXT,
            has_media INTEGER,
            media_type TEXT,
            media_path TEXT,
            media_status TEXT,
            duration_seconds REAL,
            grouped_id INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            media_type TEXT,
            file_name TEXT,
            file_path TEXT,
            mime_type TEXT,
            file_size INTEGER,
            duration_seconds REAL,
            download_status TEXT,
            FOREIGN KEY(message_id) REFERENCES posts(message_id)
        );

        CREATE INDEX IF NOT EXISTS idx_posts_message_id ON posts(message_id);
        CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date);
        CREATE INDEX IF NOT EXISTS idx_posts_media_type ON posts(media_type);
        CREATE INDEX IF NOT EXISTS idx_media_message_id ON media(message_id);
        CREATE INDEX IF NOT EXISTS idx_media_download_status ON media(download_status);
        """
        with self.conn:
            self.conn.executescript(schema_sql)

            # Migration: Ensure duration_seconds exists if table was created previously without it
            for table in ("posts", "media"):
                cursor = self.conn.cursor()
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [row["name"] for row in cursor.fetchall()]
                if "duration_seconds" not in columns:
                    self.conn.execute(f"ALTER TABLE {table} ADD COLUMN duration_seconds REAL;")

    def save_post_and_media(self, post: Post, media_items: Optional[List[MediaItem]] = None):
        """Save post and its associated media items atomically in a single transaction."""
        upsert_post_sql = """
        INSERT INTO posts (
            message_id, channel, date, text, views, forwards, replies,
            url, has_media, media_type, media_path, media_status,
            duration_seconds, grouped_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET
            channel=excluded.channel,
            date=excluded.date,
            text=excluded.text,
            views=excluded.views,
            forwards=excluded.forwards,
            replies=excluded.replies,
            url=excluded.url,
            has_media=excluded.has_media,
            media_type=excluded.media_type,
            media_path=excluded.media_path,
            media_status=excluded.media_status,
            duration_seconds=excluded.duration_seconds,
            grouped_id=excluded.grouped_id,
            created_at=excluded.created_at;
        """

        with self.conn:
            self.conn.execute(upsert_post_sql, post.to_db_tuple())

            if media_items:
                self.conn.execute("DELETE FROM media WHERE message_id = ?;", (post.message_id,))
                insert_media_sql = """
                INSERT INTO media (
                    message_id, media_type, file_name, file_path,
                    mime_type, file_size, duration_seconds, download_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """
                for item in media_items:
                    self.conn.execute(insert_media_sql, item.to_db_tuple())

    def get_processed_ids(self, channel: str) -> Set[int]:
        """Fetch all message_ids already stored for the given channel."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT message_id FROM posts WHERE channel = ?;", (channel,))
        return {row[0] for row in cursor.fetchall()}

    def get_last_processed_id(self, channel: str) -> int:
        """Fetch the highest message_id stored for the given channel."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(message_id), 0) FROM posts WHERE channel = ?;", (channel,))
        row = cursor.fetchone()
        return row[0] if row else 0

    def is_message_complete(self, message_id: int) -> bool:
        """Check if message exists and its media status is complete."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT has_media, media_status, media_type, media_path FROM posts WHERE message_id = ?;", (message_id,))
        row = cursor.fetchone()
        if not row:
            return False
        has_media, media_status, media_type, media_path = row[0], row[1], row[2], row[3]
        if not has_media:
            return True
        if media_status and media_status.startswith("skipped"):
            return True
        if media_status == "downloaded":
            if media_path:
                target = self.db_path.parent / media_path
                return target.exists() and target.stat().st_size > 0
            return False
        return False

    def cleanup_audio_and_documents(self, channel: str):
        """Reset downloaded audio, voice, and document records to skipped status."""
        with self.conn:
            self.conn.execute(
                """
                UPDATE posts
                SET media_path = NULL, media_status = 'skipped_audio'
                WHERE channel = ? AND media_type IN ('audio', 'voice');
                """,
                (channel,),
            )
            self.conn.execute(
                """
                UPDATE media
                SET file_path = '', download_status = 'skipped_audio'
                WHERE message_id IN (SELECT message_id FROM posts WHERE channel = ?)
                  AND media_type IN ('audio', 'voice');
                """,
                (channel,),
            )
            self.conn.execute(
                """
                UPDATE posts
                SET media_path = NULL, media_status = 'skipped_document'
                WHERE channel = ? AND media_type = 'document';
                """,
                (channel,),
            )
            self.conn.execute(
                """
                UPDATE media
                SET file_path = '', download_status = 'skipped_document'
                WHERE message_id IN (SELECT message_id FROM posts WHERE channel = ?)
                  AND media_type = 'document';
                """,
                (channel,),
            )

    def get_disk_usage_bytes(self) -> int:
        """Calculate total disk usage of export directory."""
        export_dir = self.db_path.parent
        total = 0
        if export_dir.exists():
            for p in export_dir.rglob("*"):
                if p.is_file():
                    try:
                        total += p.stat().st_size
                    except OSError:
                        pass
        return total

    def get_summary_stats(self, channel: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive stats:
        - total_posts
        - photos_downloaded
        - videos_detected
        - short_videos_downloaded (<= 120s)
        - long_videos_skipped (> 120s)
        - audio_skipped
        - documents_skipped
        - download_failures
        - total_downloaded_bytes
        - total_disk_usage_bytes
        """
        cursor = self.conn.cursor()

        # Total posts
        cursor.execute("SELECT COUNT(*) FROM posts WHERE channel = ?;", (channel,))
        total_posts = cursor.fetchone()[0]

        # Posts with media
        cursor.execute("SELECT COUNT(*) FROM posts WHERE channel = ? AND has_media = 1;", (channel,))
        posts_with_media = cursor.fetchone()[0]

        # Photos downloaded
        cursor.execute(
            """
            SELECT COUNT(*) FROM posts
            WHERE channel = ? AND media_type = 'photo' AND media_status = 'downloaded';
            """,
            (channel,),
        )
        photos_downloaded = cursor.fetchone()[0]

        # Videos detected
        cursor.execute(
            "SELECT COUNT(*) FROM posts WHERE channel = ? AND media_type IN ('video', 'round_video');",
            (channel,),
        )
        videos_detected = cursor.fetchone()[0]

        # Short videos downloaded (<= 120s)
        cursor.execute(
            """
            SELECT COUNT(*) FROM posts
            WHERE channel = ? AND media_type IN ('video', 'round_video')
              AND media_status = 'downloaded';
            """,
            (channel,),
        )
        short_videos_downloaded = cursor.fetchone()[0]

        # Long videos skipped (> 120s)
        cursor.execute(
            """
            SELECT COUNT(*) FROM posts
            WHERE channel = ? AND media_status = 'skipped_duration';
            """,
            (channel,),
        )
        long_videos_skipped = cursor.fetchone()[0]

        # Audio skipped (both audio and voice)
        cursor.execute(
            """
            SELECT COUNT(*) FROM posts
            WHERE channel = ? AND (
                media_status IN ('skipped_audio', 'skipped_voice')
                OR (media_type IN ('audio', 'voice') AND media_status LIKE 'skipped%')
            );
            """,
            (channel,),
        )
        audio_skipped = cursor.fetchone()[0]

        # Documents skipped
        cursor.execute(
            """
            SELECT COUNT(*) FROM posts
            WHERE channel = ? AND (
                media_status = 'skipped_document'
                OR (media_type = 'document' AND media_status LIKE 'skipped%')
            );
            """,
            (channel,),
        )
        documents_skipped = cursor.fetchone()[0]

        # Total media downloaded
        cursor.execute(
            """
            SELECT COUNT(*) FROM media m
            JOIN posts p ON m.message_id = p.message_id
            WHERE p.channel = ? AND m.download_status = 'downloaded';
            """,
            (channel,),
        )
        media_downloaded = cursor.fetchone()[0]

        # Download failures
        cursor.execute(
            """
            SELECT COUNT(*) FROM media m
            JOIN posts p ON m.message_id = p.message_id
            WHERE p.channel = ? AND m.download_status = 'failed';
            """,
            (channel,),
        )
        download_failures = cursor.fetchone()[0]

        # Total downloaded bytes (recorded in media table for completed downloads)
        cursor.execute(
            """
            SELECT COALESCE(SUM(m.file_size), 0) FROM media m
            JOIN posts p ON m.message_id = p.message_id
            WHERE p.channel = ? AND m.download_status = 'downloaded';
            """,
            (channel,),
        )
        total_bytes = cursor.fetchone()[0]

        total_disk_usage = self.get_disk_usage_bytes()

        return {
            "total_posts": total_posts,
            "posts_with_media": posts_with_media,
            "photos_downloaded": photos_downloaded,
            "videos_detected": videos_detected,
            "short_videos_downloaded": short_videos_downloaded,
            "long_videos_skipped": long_videos_skipped,
            "audio_skipped": audio_skipped,
            "documents_skipped": documents_skipped,
            "media_downloaded": media_downloaded,
            "download_failures": download_failures,
            "total_bytes": total_bytes,
            "total_gb": total_bytes / (1024 ** 3),
            "total_disk_usage_bytes": total_disk_usage,
            "total_disk_usage_mb": total_disk_usage / (1024 * 1024),
            "total_disk_usage_gb": total_disk_usage / (1024 ** 3),
        }

    def get_stats(self, channel: str) -> Dict[str, int]:
        """Backward compatible stats helper."""
        s = self.get_summary_stats(channel)
        return {
            "total_posts": s["total_posts"],
            "posts_with_media": s["posts_with_media"],
            "media_downloaded": s["media_downloaded"],
            "media_failed": s["download_failures"],
            "long_videos_skipped": s["long_videos_skipped"],
        }

    def run_integrity_check(self) -> Tuple[bool, List[str]]:
        """
        Execute PRAGMA integrity_check; to verify database consistency.
        Returns: (is_healthy, messages)
        """
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        rows = cursor.fetchall()
        messages = [row[0] for row in rows]
        is_healthy = len(messages) == 1 and messages[0].lower() == "ok"
        return is_healthy, messages

    def close(self):
        """Close SQLite connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
