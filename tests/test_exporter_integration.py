"""Integration test mocking Telethon MTProto messages to verify SQLite export & media downloads."""

import sys
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telethon.tl.types import (
    Message,
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaPoll,
    Document,
    DocumentAttributeFilename,
    DocumentAttributeVideo,
    DocumentAttributeAnimated,
    Poll,
    PollAnswer,
)
from database import Database
from exporter import ChannelExporter
from progress import ExporterProgressUI


class TestExporterIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.export_dir = Path(self.temp_dir) / "export"
        self.db = Database(self.export_dir / "telegram_archive.db")
        self.db.connect()

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)

    def _create_mock_message(
        self,
        msg_id: int,
        text: str,
        media=None,
        views=100,
        grouped_id=None,
    ):
        msg = MagicMock(spec=Message)
        msg.id = msg_id
        msg.text = text
        msg.raw_text = text
        msg.date = datetime(2026, 9, 13, 12, 30, 0, tzinfo=timezone.utc)
        msg.views = views
        msg.forwards = 10
        msg.replies = None
        msg.media = media
        msg.grouped_id = grouped_id
        return msg

    async def test_full_sqlite_export_and_media_pipeline(self):
        client_mock = MagicMock()

        # Mock download_media: writes dummy binary data
        async def fake_download(msg, file):
            target_path = Path(file)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(b"sample binary media bytes")
            return str(target_path)

        client_mock.download_media = AsyncMock(side_effect=fake_download)

        # 1. Text message
        msg1 = self._create_mock_message(1, "Welcome to @kalkastop!")

        # 2. Photo message
        photo_media = MagicMock(spec=MessageMediaPhoto)
        msg2 = self._create_mock_message(2, "Grammar diagram", media=photo_media)

        # 3. Document message (PDF)
        doc = MagicMock(spec=Document)
        doc.mime_type = "application/pdf"
        doc_filename_attr = MagicMock(spec=DocumentAttributeFilename)
        doc_filename_attr.file_name = "rules.pdf"
        doc.attributes = [doc_filename_attr]
        doc_media = MagicMock(spec=MessageMediaDocument)
        doc_media.document = doc
        msg3 = self._create_mock_message(3, "PDF Document", media=doc_media)

        # 4. Animated GIF message
        anim_doc = MagicMock(spec=Document)
        anim_doc.mime_type = "image/gif"
        anim_attr = MagicMock(spec=DocumentAttributeAnimated)
        anim_doc.attributes = [anim_attr]
        anim_media = MagicMock(spec=MessageMediaDocument)
        anim_media.document = anim_doc
        msg4 = self._create_mock_message(4, "Funny animated explanation", media=anim_media)

        async def iter_messages_mock(entity, reverse=True, min_id=0):
            for m in [msg1, msg2, msg3, msg4]:
                if m.id > min_id:
                    yield m

        client_mock.iter_messages = MagicMock(side_effect=iter_messages_mock)
        entity_mock = MagicMock()

        ui = ExporterProgressUI(channel_title="Kalka Stop", channel_username="kalkastop", total_estimated=4)

        exporter = ChannelExporter(
            client=client_mock,
            entity=entity_mock,
            channel_title="Kalka Stop",
            channel_username="kalkastop",
            export_dir=self.export_dir,
            db=self.db,
            download_media=True,
            progress_ui=ui,
        )

        await exporter.run()

        # Check in-memory counters
        self.assertEqual(exporter.posts_saved, 4)
        self.assertEqual(exporter.media_downloaded, 1)  # only photo downloaded
        self.assertEqual(exporter.photos_downloaded, 1)
        self.assertEqual(exporter.documents_skipped, 1)
        self.assertEqual(exporter.media_failed, 0)

        # Check SQLite Database tables
        cursor = self.db.conn.cursor()

        # Posts table verification
        cursor.execute("SELECT COUNT(*) FROM posts;")
        self.assertEqual(cursor.fetchone()[0], 4)

        cursor.execute("SELECT message_id, media_type, media_path, media_status FROM posts WHERE message_id = 2;")
        p2 = cursor.fetchone()
        self.assertEqual(p2["media_type"], "photo")
        self.assertEqual(p2["media_path"], "media/images/2.jpg")
        self.assertEqual(p2["media_status"], "downloaded")

        # Media table verification
        cursor.execute("SELECT COUNT(*) FROM media WHERE download_status = 'downloaded';")
        self.assertEqual(cursor.fetchone()[0], 1)

        cursor.execute("SELECT file_path, download_status FROM media WHERE message_id = 3;")
        m3 = cursor.fetchone()
        self.assertEqual(m3["download_status"], "skipped_document")
        self.assertEqual(m3["file_path"], "")

        cursor.execute("SELECT file_path, media_type, download_status FROM media WHERE message_id = 4;")
        m4 = cursor.fetchone()
        self.assertEqual(m4["media_type"], "animation")
        self.assertEqual(m4["download_status"], "skipped")
        self.assertEqual(m4["file_path"], "")

        # Verify physical files exist on disk: only photo, documents/animations not downloaded
        self.assertTrue((self.export_dir / "media" / "images" / "2.jpg").exists())
        self.assertFalse((self.export_dir / "media" / "documents" / "3_rules.pdf").exists())
        self.assertFalse((self.export_dir / "media" / "animations" / "4.mp4").exists())

        # Verify PRAGMA integrity_check
        is_ok, msgs = self.db.run_integrity_check()
        self.assertTrue(is_ok)
        self.assertEqual(msgs, ["ok"])


if __name__ == "__main__":
    unittest.main()
