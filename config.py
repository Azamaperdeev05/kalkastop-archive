"""Configuration management for Telegram Channel Exporter."""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# Automatically load environment variables from .env
load_dotenv(BASE_DIR / ".env")


def str_to_bool(val: str) -> bool:
    """Helper to convert string or boolean values to bool."""
    if isinstance(val, bool):
        return val
    if not val:
        return False
    return val.strip().lower() in ("true", "1", "yes", "y", "t")


@dataclass
class Config:
    api_id: int
    api_hash: str
    download_media: bool
    session_name: str
    export_dir: Path

    @classmethod
    def load(cls, cli_download_media: bool | None = None) -> "Config":
        raw_api_id = os.getenv("API_ID", "").strip()
        api_hash = os.getenv("API_HASH", "").strip()

        # Parse API_ID
        try:
            api_id = int(raw_api_id) if raw_api_id else 0
        except ValueError:
            api_id = 0

        # CLI flag overrides .env if explicitly provided
        if cli_download_media is not None:
            download_media = cli_download_media
        else:
            download_media = str_to_bool(os.getenv("DOWNLOAD_MEDIA", "true"))

        session_name = os.getenv("SESSION_NAME", "telegram_exporter").strip() or "telegram_exporter"

        raw_export_dir = os.getenv("EXPORT_DIR", "export").strip() or "export"
        export_path = Path(raw_export_dir)
        if not export_path.is_absolute():
            export_path = BASE_DIR / export_path

        return cls(
            api_id=api_id,
            api_hash=api_hash,
            download_media=download_media,
            session_name=session_name,
            export_dir=export_path,
        )

    def validate(self) -> tuple[bool, str]:
        """Validate presence of critical MTProto credentials."""
        if not self.api_id or not self.api_hash:
            return (
                False,
                "Missing or invalid API_ID and API_HASH in your .env file.\n\n"
                "To resolve this:\n"
                "1. Visit https://my.telegram.org and log in with your phone number.\n"
                "2. Go to 'API development tools'.\n"
                "3. Create an application if you haven't already to get your 'api_id' and 'api_hash'.\n"
                "4. Copy .env.example to .env and fill in your credentials:\n"
                "   API_ID=your_api_id\n"
                "   API_HASH=your_api_hash\n"
            )
        return True, ""
