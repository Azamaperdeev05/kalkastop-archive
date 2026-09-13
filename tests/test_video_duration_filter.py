"""Unit test specifically verifying video duration filtering logic (<=120s downloaded, >120s skipped)."""

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
    Document,
    DocumentAttributeVideo,
    DocumentAttributeAudio,
    DocumentAttributeFilename,
)
from database import Database
from exporter import ChannelExporter
from progress import ExporterProgressUI


class TestVideoDurationFilter(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.export_dir = Path(self.temp_dir) / "export"
        self.db = Database(self.export_dir / "telegram_archive.db")
        self.db.connect()

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)

    def _create_mock_video_message(self, msg_id: int, text: str, duration_sec: float, file_size: int = 1000000):
        msg = MagicMock(spec=Message)
        msg.id = msg_id
        msg.text = text
        msg.raw_text = text
        msg.date = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)
        msg.views = 200
        msg.forwards = 5
        msg.replies = None
        msg.grouped_id = None

        doc = MagicMock(spec=Document)
        doc.mime_type = "video/mp4"
        video_attr = MagicMock(spec=DocumentAttributeVideo)
        video_attr.duration = duration_sec
        video_attr.round_message = False
        doc.attributes = [video_attr]

        media_doc = MagicMock(spec=MessageMediaDocument)
        media_doc.document = doc
        msg.media = media_doc

        file_mock = MagicMock()
        file_mock.size = file_size
        msg.file = file_mock
        return msg

    async def test_video_duration_filter_rules(self):
        client_mock = MagicMock()

        downloaded_msg_ids = []

        async def fake_download(msg, file):
            downloaded_msg_ids.append(msg.id)
            target_path = Path(file)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(b"mp4 video bytes")
            return str(target_path)

        client_mock.download_media = AsyncMock(side_effect=fake_download)

        # Video 1: Short video (45s <= 120s) -> MUST be downloaded
        v_short = self._create_mock_video_message(101, "Short grammar clip", duration_sec=45.0)

        # Video 2: Exact boundary video (120s <= 120s) -> MUST be downloaded
        v_boundary = self._create_mock_video_message(102, "Two minute clip", duration_sec=120.0)

        # Video 3: Long video (301s > 120s) -> MUST be SKIPPED
        v_long = self._create_mock_video_message(103, "Five minute lesson", duration_sec=301.0)

        # Video 4: Extremely long video (1800s > 120s) -> MUST be SKIPPED
        v_huge = self._create_mock_video_message(104, "Half hour lecture", duration_sec=1800.0)

        async def iter_mock(entity, reverse=True, min_id=0):
            for m in [v_short, v_boundary, v_long, v_huge]:
                if m.id > min_id:
                    yield m

        client_mock.iter_messages = MagicMock(side_effect=iter_mock)
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
            max_video_duration=120.0,
            progress_ui=ui,
        )

        await exporter.run()

        # Check which messages had download_media called
        self.assertEqual(downloaded_msg_ids, [101, 102])
        self.assertNotIn(103, downloaded_msg_ids)
        self.assertNotIn(104, downloaded_msg_ids)

        # Verify disk files
        self.assertTrue((self.export_dir / "media" / "videos" / "101.mp4").exists())
        self.assertTrue((self.export_dir / "media" / "videos" / "102.mp4").exists())
        self.assertFalse((self.export_dir / "media" / "videos" / "103.mp4").exists())
        self.assertFalse((self.export_dir / "media" / "videos" / "104.mp4").exists())

        # Verify SQLite posts table
        cursor = self.db.conn.cursor()

        cursor.execute("SELECT message_id, media_status, duration_seconds, media_path FROM posts WHERE message_id = 101;")
        r101 = cursor.fetchone()
        self.assertEqual(r101["media_status"], "downloaded")
        self.assertEqual(r101["duration_seconds"], 45.0)
        self.assertEqual(r101["media_path"], "media/videos/101.mp4")

        cursor.execute("SELECT message_id, media_status, duration_seconds, media_path FROM posts WHERE message_id = 103;")
        r103 = cursor.fetchone()
        self.assertEqual(r103["media_status"], "skipped_duration")
        self.assertEqual(r103["duration_seconds"], 301.0)
        self.assertIsNone(r103["media_path"])

        cursor.execute("SELECT message_id, media_status, duration_seconds, media_path FROM posts WHERE message_id = 104;")
        r104 = cursor.fetchone()
        self.assertEqual(r104["media_status"], "skipped_duration")
        self.assertEqual(r104["duration_seconds"], 1800.0)

        # Verify SQLite media table
        cursor.execute("SELECT message_id, download_status, duration_seconds FROM media WHERE message_id = 103;")
        m103 = cursor.fetchone()
        self.assertIsNotNone(m103)
        self.assertEqual(m103["download_status"], "skipped_duration")
        self.assertEqual(m103["duration_seconds"], 301.0)

        # Verify summary stats
        stats = self.db.get_summary_stats("kalkastop")
        self.assertEqual(stats["total_posts"], 4)
        self.assertEqual(stats["videos_detected"], 4)
        self.assertEqual(stats["short_videos_downloaded"], 2)
        self.assertEqual(stats["long_videos_skipped"], 2)
        self.assertEqual(stats["download_failures"], 0)

        # Verify PRAGMA integrity_check
        is_ok, msgs = self.db.run_integrity_check()
        self.assertTrue(is_ok)
        self.assertEqual(msgs, ["ok"])

    async def test_audio_and_documents_skipped_and_photos_downloaded(self):
        client_mock = MagicMock()
        downloaded_msg_ids = []

        async def fake_download(msg, file):
            downloaded_msg_ids.append(msg.id)
            target_path = Path(file)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(b"sample bytes")
            return str(target_path)

        client_mock.download_media = AsyncMock(side_effect=fake_download)

        # 1. Photo -> DOWNLOAD
        photo_media = MagicMock(spec=MessageMediaPhoto)
        p_msg = MagicMock(spec=Message)
        p_msg.id = 201
        p_msg.text = "Photo caption"
        p_msg.raw_text = "Photo caption"
        p_msg.date = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)
        p_msg.views = 100
        p_msg.forwards = 1
        p_msg.replies = None
        p_msg.grouped_id = None
        p_msg.media = photo_media
        p_msg.file = MagicMock(size=50000)

        # 2. Audio -> SKIP download, save metadata
        audio_doc = MagicMock(spec=Document)
        audio_doc.mime_type = "audio/mpeg"
        audio_attr = MagicMock(spec=DocumentAttributeAudio)
        audio_attr.duration = 240.0
        audio_attr.voice = False
        audio_doc.attributes = [audio_attr]
        a_media = MagicMock(spec=MessageMediaDocument)
        a_media.document = audio_doc
        a_msg = MagicMock(spec=Message)
        a_msg.id = 202
        a_msg.text = "Audio podcast"
        a_msg.raw_text = "Audio podcast"
        a_msg.date = datetime(2026, 9, 14, 12, 1, 0, tzinfo=timezone.utc)
        a_msg.views = 150
        a_msg.forwards = 2
        a_msg.replies = None
        a_msg.grouped_id = None
        a_msg.media = a_media
        a_msg.file = MagicMock(size=5000000)

        # 3. Document (PDF) -> SKIP download, save metadata
        doc = MagicMock(spec=Document)
        doc.mime_type = "application/pdf"
        doc_filename_attr = MagicMock(spec=DocumentAttributeFilename)
        doc_filename_attr.file_name = "test.pdf"
        doc.attributes = [doc_filename_attr]
        d_media = MagicMock(spec=MessageMediaDocument)
        d_media.document = doc
        d_msg = MagicMock(spec=Message)
        d_msg.id = 203
        d_msg.text = "Document PDF"
        d_msg.raw_text = "Document PDF"
        d_msg.date = datetime(2026, 9, 14, 12, 2, 0, tzinfo=timezone.utc)
        d_msg.views = 200
        d_msg.forwards = 3
        d_msg.replies = None
        d_msg.grouped_id = None
        d_msg.media = d_media
        d_msg.file = MagicMock(size=1200000)

        async def iter_mock(entity, reverse=True, min_id=0):
            for m in [p_msg, a_msg, d_msg]:
                if m.id > min_id:
                    yield m

        client_mock.iter_messages = MagicMock(side_effect=iter_mock)
        entity_mock = MagicMock()

        exporter = ChannelExporter(
            client=client_mock,
            entity=entity_mock,
            channel_title="Kalka Stop",
            channel_username="kalkastop",
            export_dir=self.export_dir,
            db=self.db,
            download_media=True,
            max_video_duration=120.0,
        )

        await exporter.run()

        # Only photo should be downloaded!
        self.assertEqual(downloaded_msg_ids, [201])
        self.assertTrue((self.export_dir / "media" / "images" / "201.jpg").exists())
        self.assertFalse((self.export_dir / "media" / "audio" / "202.mp3").exists())
        self.assertFalse((self.export_dir / "media" / "documents" / "203_test.pdf").exists())

        # Verify summary stats
        stats = self.db.get_summary_stats("kalkastop")
        self.assertEqual(stats["total_posts"], 3)
        self.assertEqual(stats["photos_downloaded"], 1)
        self.assertEqual(stats["audio_skipped"], 1)
        self.assertEqual(stats["documents_skipped"], 1)


if __name__ == "__main__":
    unittest.main()
