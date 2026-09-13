"""Unit tests for exporter.py file system operations, media classification, and SQLite state loading."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from database import Database
from exporter import ChannelExporter, sanitize_filename
from models import Post, MediaItem


class TestExporterLogic(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.export_dir = Path(self.temp_dir) / "export"
        self.db = Database(self.export_dir / "telegram_archive.db")
        self.db.connect()

        self.client_mock = MagicMock()
        self.entity_mock = MagicMock()
        self.exporter = ChannelExporter(
            client=self.client_mock,
            entity=self.entity_mock,
            channel_title="Kalka Stop",
            channel_username="kalkastop",
            export_dir=self.export_dir,
            db=self.db,
            download_media=True,
        )

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("valid_name-123.jpg"), "valid_name-123.jpg")
        self.assertEqual(sanitize_filename("bad/name:?*|.pdf"), "badname.pdf")
        self.assertEqual(sanitize_filename("   "), "file")

    def test_init_filesystem(self):
        self.exporter.init_filesystem()
        self.assertTrue(self.export_dir.exists())
        self.assertTrue((self.export_dir / "media" / "images").exists())
        self.assertTrue((self.export_dir / "media" / "videos").exists())
        self.assertTrue((self.export_dir / "media" / "documents").exists())
        self.assertTrue((self.export_dir / "media" / "audio").exists())
        self.assertTrue((self.export_dir / "media" / "voice").exists())
        self.assertTrue((self.export_dir / "media" / "animations").exists())
        self.assertTrue((self.export_dir / "media" / "other").exists())

    def test_load_state_from_db(self):
        self.exporter.init_filesystem()
        post = Post(
            message_id=50,
            channel="kalkastop",
            date="2026-09-14T00:00:00+00:00",
            text="Test post",
            has_media=1,
            media_type="photo",
            media_path="media/images/50.jpg",
            media_status="downloaded",
        )
        media_item = MediaItem(
            message_id=50,
            media_type="photo",
            file_name="50.jpg",
            file_path="media/images/50.jpg",
            download_status="downloaded",
        )
        self.db.save_post_and_media(post, [media_item])

        new_exporter = ChannelExporter(
            client=self.client_mock,
            entity=self.entity_mock,
            channel_title="Kalka Stop",
            channel_username="kalkastop",
            export_dir=self.export_dir,
            db=self.db,
            download_media=True,
        )
        new_exporter.load_state_from_db()

        self.assertEqual(new_exporter.last_processed_id, 50)
        self.assertIn(50, new_exporter.processed_ids)
        self.assertEqual(new_exporter.posts_saved, 1)
        self.assertEqual(new_exporter.media_downloaded, 1)


if __name__ == "__main__":
    unittest.main()
