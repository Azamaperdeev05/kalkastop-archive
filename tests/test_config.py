"""Unit tests for config.py."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch
from config import Config, str_to_bool


class TestConfig(unittest.TestCase):
    def test_str_to_bool(self):
        self.assertTrue(str_to_bool("true"))
        self.assertTrue(str_to_bool("True"))
        self.assertTrue(str_to_bool("1"))
        self.assertTrue(str_to_bool("yes"))
        self.assertTrue(str_to_bool("Y"))
        self.assertFalse(str_to_bool("false"))
        self.assertFalse(str_to_bool("0"))
        self.assertFalse(str_to_bool("no"))
        self.assertFalse(str_to_bool(""))

    def test_config_validation_failure(self):
        with patch.dict(os.environ, {"API_ID": "", "API_HASH": ""}, clear=True):
            cfg = Config.load()
            valid, msg = cfg.validate()
            self.assertFalse(valid)
            self.assertIn("Missing or invalid API_ID", msg)

    def test_config_validation_success(self):
        with patch.dict(
            os.environ,
            {
                "API_ID": "123456",
                "API_HASH": "abcdef0123456789abcdef0123456789",
                "DOWNLOAD_MEDIA": "true",
            },
            clear=True,
        ):
            cfg = Config.load()
            valid, msg = cfg.validate()
            self.assertTrue(valid)
            self.assertEqual(cfg.api_id, 123456)
            self.assertEqual(cfg.api_hash, "abcdef0123456789abcdef0123456789")
            self.assertTrue(cfg.download_media)

    def test_cli_override_download_media(self):
        with patch.dict(os.environ, {"DOWNLOAD_MEDIA": "false"}, clear=True):
            cfg = Config.load(cli_download_media=True)
            self.assertTrue(cfg.download_media)


if __name__ == "__main__":
    unittest.main()
