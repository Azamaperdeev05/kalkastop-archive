"""Unit tests for SQLite database operations in database.py."""

import shutil
import tempfile
import unittest
from pathlib import Path

from database import Database
from models import Post, MediaItem


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_archive.db"
        self.db = Database(self.db_path)
        self.db.connect()

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)

    def test_schema_creation_and_pragmas(self):
        cursor = self.db.conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        self.assertEqual(mode.lower(), "wal")

        cursor.execute("PRAGMA foreign_keys;")
        fk = cursor.fetchone()[0]
        self.assertEqual(fk, 1)

        # Check table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        self.assertIn("posts", tables)
        self.assertIn("media", tables)

    def test_save_post_and_media_with_foreign_key(self):
        post = Post(
            message_id=101,
            channel="kalkastop",
            date="2026-09-14T00:00:00+00:00",
            text="Post with photo",
            views=500,
            forwards=10,
            has_media=1,
            media_type="photo",
            media_path="media/images/101.jpg",
            media_status="downloaded",
        )
        media_item = MediaItem(
            message_id=101,
            media_type="photo",
            file_name="101.jpg",
            file_path="media/images/101.jpg",
            mime_type="image/jpeg",
            file_size=12345,
            download_status="downloaded",
        )

        self.db.save_post_and_media(post, [media_item])

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT message_id, channel, text, has_media FROM posts WHERE message_id = 101;")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["message_id"], 101)
        self.assertEqual(row["channel"], "kalkastop")
        self.assertEqual(row["has_media"], 1)

        cursor.execute("SELECT message_id, file_path, file_size FROM media WHERE message_id = 101;")
        m_row = cursor.fetchone()
        self.assertIsNotNone(m_row)
        self.assertEqual(m_row["file_path"], "media/images/101.jpg")
        self.assertEqual(m_row["file_size"], 12345)

    def test_duplicate_prevention_on_conflict(self):
        post1 = Post(
            message_id=200,
            channel="kalkastop",
            date="2026-09-14T00:00:00+00:00",
            text="Initial text",
            views=100,
        )
        self.db.save_post_and_media(post1)

        # Update with new views and updated text
        post2 = Post(
            message_id=200,
            channel="kalkastop",
            date="2026-09-14T00:00:00+00:00",
            text="Updated text",
            views=150,
        )
        self.db.save_post_and_media(post2)

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM posts WHERE message_id = 200;")
        self.assertEqual(cursor.fetchone()[0], 1)

        cursor.execute("SELECT text, views FROM posts WHERE message_id = 200;")
        row = cursor.fetchone()
        self.assertEqual(row["text"], "Updated text")
        self.assertEqual(row["views"], 150)

    def test_resume_helpers(self):
        p1 = Post(message_id=1, channel="kalkastop", date="2026-01-01", text="p1")
        p2 = Post(message_id=5, channel="kalkastop", date="2026-01-02", text="p2")
        self.db.save_post_and_media(p1)
        self.db.save_post_and_media(p2)

        processed = self.db.get_processed_ids("kalkastop")
        self.assertEqual(processed, {1, 5})

        last_id = self.db.get_last_processed_id("kalkastop")
        self.assertEqual(last_id, 5)

    def test_integrity_check(self):
        is_ok, msgs = self.db.run_integrity_check()
        self.assertTrue(is_ok)
        self.assertEqual(msgs, ["ok"])

    def test_stats(self):
        p = Post(
            message_id=10,
            channel="kalkastop",
            date="2026-01-01",
            text="media post",
            has_media=1,
        )
        m = MediaItem(
            message_id=10,
            media_type="photo",
            file_name="10.jpg",
            file_path="media/images/10.jpg",
            download_status="downloaded",
        )
        self.db.save_post_and_media(p, [m])

        stats = self.db.get_stats("kalkastop")
        self.assertEqual(stats["total_posts"], 1)
        self.assertEqual(stats["posts_with_media"], 1)
        self.assertEqual(stats["media_downloaded"], 1)
        self.assertEqual(stats["media_failed"], 0)


if __name__ == "__main__":
    unittest.main()
