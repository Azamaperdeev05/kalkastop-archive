"""Unit tests for models.py."""

import unittest
from models import Post, MediaItem, CSV_FIELDNAMES


class TestPostModel(unittest.TestCase):
    def test_post_to_dict_matches_expected_schema(self):
        post = Post(
            message_id=123,
            channel="kalkastop",
            date="2026-09-13T12:30:00+05:00",
            text="Example post text",
            views=1520,
            forwards=42,
            replies=5,
            has_media=1,
            media_type="photo",
            media_path="media/images/123.jpg",
            media_status="downloaded",
            url="https://t.me/kalkastop/123",
        )
        d = post.to_dict()

        self.assertEqual(d["message_id"], 123)
        self.assertEqual(d["channel"], "kalkastop")
        self.assertEqual(d["date"], "2026-09-13T12:30:00+05:00")
        self.assertEqual(d["text"], "Example post text")
        self.assertEqual(d["views"], 1520)
        self.assertEqual(d["forwards"], 42)
        self.assertEqual(d["replies"], 5)
        self.assertTrue(d["has_media"])
        self.assertEqual(d["media_type"], "photo")
        self.assertEqual(d["media_path"], "media/images/123.jpg")
        self.assertEqual(d["url"], "https://t.me/kalkastop/123")

    def test_post_to_csv_row(self):
        post = Post(
            message_id=456,
            channel="kalkastop",
            date="2026-09-13T14:00:00+05:00",
            text="Text message",
            views=100,
            has_media=0,
            url="https://t.me/kalkastop/456",
        )
        row = post.to_csv_row()
        for field in CSV_FIELDNAMES:
            self.assertIn(field, row)

        self.assertEqual(row["message_id"], 456)
        self.assertEqual(row["text"], "Text message")
        self.assertEqual(row["views"], 100)
        self.assertEqual(row["has_media"], 0)
        self.assertEqual(row["media_type"], "")
        self.assertEqual(row["media_path"], "")

    def test_media_item(self):
        item = MediaItem(
            message_id=500,
            media_type="video",
            file_name="500.mp4",
            file_path="media/videos/500.mp4",
            mime_type="video/mp4",
            file_size=1048576,
            download_status="downloaded",
        )
        tup = item.to_db_tuple()
        self.assertEqual(tup[0], 500)
        self.assertEqual(tup[1], "video")
        self.assertEqual(tup[2], "500.mp4")
        self.assertEqual(tup[3], "media/videos/500.mp4")
        self.assertEqual(tup[4], "video/mp4")
        self.assertIsNone(tup[6])  # duration_seconds
        self.assertEqual(tup[7], "downloaded")


if __name__ == "__main__":
    unittest.main()
