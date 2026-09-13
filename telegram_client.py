"""Telegram client connection, authentication, and channel resolution."""

import re
from pathlib import Path
from typing import Optional, Tuple, Any
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.errors import (
    ChannelPrivateError,
    UsernameNotOccupiedError,
    UsernameInvalidError,
)


def extract_channel_identifier(input_val: str) -> str:
    """
    Extract clean channel identifier from various input formats:
    - @kalkastop -> kalkastop
    - https://t.me/kalkastop -> kalkastop
    - https://t.me/kalkastop/123 -> kalkastop
    - t.me/kalkastop -> kalkastop
    - kalkastop -> kalkastop
    - https://telegram.me/joinchat/... -> raw string
    """
    trimmed = input_val.strip()
    if not trimmed:
        return ""

    # Remove t.me / telegram.me URLs
    url_match = re.match(r"^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(?:s/)?([a-zA-Z0-9_]+)(?:/\d+)?/?$", trimmed)
    if url_match:
        return url_match.group(1)

    # Remove leading @
    if trimmed.startswith("@"):
        return trimmed[1:]

    return trimmed


class TelegramConnection:
    """Wrapper around Telethon TelegramClient for interactive auth and channel access."""

    def __init__(self, api_id: int, api_hash: str, session_path: Path):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = str(session_path)
        self.client: Optional[TelegramClient] = None

    async def connect(self) -> TelegramClient:
        """Initialize the Telethon client and authenticate interactively if needed."""
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
        # client.start() automatically prompts for phone, code, and 2FA password in terminal
        await self.client.start()
        return self.client

    async def resolve_channel(self, channel_input: str) -> Tuple[Any, str, str, Optional[int]]:
        """
        Resolves the user channel input to a Telegram entity.
        Returns:
            (entity, channel_username_or_title, clean_slug, total_messages_count)
        """
        if not self.client:
            raise RuntimeError("Telegram client is not connected.")

        channel_identifier = extract_channel_identifier(channel_input)
        if not channel_identifier:
            raise ValueError(f"Invalid channel input: '{channel_input}'")

        try:
            entity = await self.client.get_entity(channel_identifier)
        except (UsernameNotOccupiedError, UsernameInvalidError) as e:
            raise ValueError(f"Channel '{channel_identifier}' was not found: {e}")
        except ChannelPrivateError as e:
            raise PermissionError(f"Channel '{channel_identifier}' is private or you do not have access: {e}")

        # Check entity type
        if not isinstance(entity, (Channel, Chat)):
            raise ValueError(
                f"The specified entity '{channel_identifier}' is a {type(entity).__name__}, not a Telegram channel or chat."
            )

        title = getattr(entity, "title", str(channel_identifier))
        username = getattr(entity, "username", None) or channel_identifier

        # Get total messages count if possible
        total_count: Optional[int] = None
        try:
            result = await self.client.get_messages(entity, limit=0)
            total_count = result.total
        except Exception:
            total_count = None

        return entity, title, username, total_count

    async def disconnect(self):
        """Cleanly disconnect client."""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
