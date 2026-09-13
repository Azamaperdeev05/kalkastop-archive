"""Unit tests for telegram_client.py channel identifier extraction."""

import unittest
from telegram_client import extract_channel_identifier


class TestChannelIdentifier(unittest.TestCase):
    def test_standard_username(self):
        self.assertEqual(extract_channel_identifier("kalkastop"), "kalkastop")

    def test_username_with_at_prefix(self):
        self.assertEqual(extract_channel_identifier("@kalkastop"), "kalkastop")

    def test_https_t_me_url(self):
        self.assertEqual(extract_channel_identifier("https://t.me/kalkastop"), "kalkastop")
        self.assertEqual(extract_channel_identifier("http://t.me/kalkastop/"), "kalkastop")

    def test_https_t_me_s_preview_url(self):
        self.assertEqual(extract_channel_identifier("https://t.me/s/kalkastop"), "kalkastop")

    def test_https_telegram_me_url(self):
        self.assertEqual(extract_channel_identifier("https://telegram.me/kalkastop"), "kalkastop")

    def test_url_with_message_id_suffix(self):
        self.assertEqual(extract_channel_identifier("https://t.me/kalkastop/123"), "kalkastop")

    def test_whitespace_handling(self):
        self.assertEqual(extract_channel_identifier("  @kalkastop \n"), "kalkastop")

    def test_empty_string(self):
        self.assertEqual(extract_channel_identifier(""), "")


if __name__ == "__main__":
    unittest.main()
