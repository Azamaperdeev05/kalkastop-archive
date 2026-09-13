"""Unit tests for progress.py."""

import unittest
from progress import format_elapsed, ExporterProgressUI


class TestProgressUI(unittest.TestCase):
    def test_format_elapsed(self):
        self.assertEqual(format_elapsed(45), "00:45")
        self.assertEqual(format_elapsed(125), "02:05")
        self.assertEqual(format_elapsed(3665), "01:01:05")

    def test_ui_renderable_creation(self):
        ui = ExporterProgressUI(
            channel_title="Test Channel",
            channel_username="testchannel",
            total_estimated=100,
        )
        ui.update(
            posts_processed=50,
            posts_saved=50,
            media_found=25,
            media_downloaded=25,
            media_failed=0,
            current_message_id=50,
        )
        panel = ui._generate_renderable()
        self.assertIsNotNone(panel)
        self.assertIn("Test Channel", panel.subtitle)


if __name__ == "__main__":
    unittest.main()
