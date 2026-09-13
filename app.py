"""Telegram Channel Exporter CLI application (SQLite + Video Duration Filter)."""

import sys
import signal
import asyncio
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt

from config import Config
from database import Database
from telegram_client import TelegramConnection
from exporter import ChannelExporter
from progress import ExporterProgressUI

console = Console()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export all posts and media from a Telegram channel into a local SQLite database with video duration filter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python app.py\n"
            "  python app.py --channel @kalkastop\n"
            "  python app.py --channel @kalkastop --max-video-duration 120\n"
        ),
    )
    parser.add_argument(
        "-c", "--channel",
        type=str,
        default=None,
        help="Target channel username or URL (e.g. @kalkastop, https://t.me/kalkastop, or kalkastop)",
    )
    parser.add_argument(
        "--max-video-duration",
        type=float,
        default=120.0,
        help="Maximum video duration in seconds to download (default: 120s / 2 minutes)",
    )
    parser.add_argument(
        "--download-media",
        action="store_true",
        default=True,
        help="Download photos, documents, audio, and short videos <= max duration (default: True)",
    )
    parser.add_argument(
        "--no-download-media",
        action="store_false",
        dest="download_media",
        help="Disable media downloading (export text and metadata only)",
    )
    parser.add_argument(
        "-o", "--export-dir",
        type=str,
        default=None,
        help="Directory to save SQLite database and media (default: ./export)",
    )
    return parser.parse_args()


async def main_async():
    args = parse_arguments()

    # Banner
    console.print("[bold cyan]════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold yellow]   Telegram Channel Exporter (SQLite Archive + Media Filter)[/bold yellow]")
    console.print("[bold cyan]════════════════════════════════════════════════════════════[/bold cyan]\n")

    # Load configuration
    config = Config.load(cli_download_media=args.download_media)

    # Override export dir if provided
    if args.export_dir:
        config.export_dir = Path(args.export_dir)
        if not config.export_dir.is_absolute():
            config.export_dir = Path.cwd() / config.export_dir

    # Validate credentials
    valid, error_message = config.validate()
    if not valid:
        console.print(f"[bold red]Configuration Error:[/bold red]\n{error_message}")
        sys.exit(1)

    # Target channel input
    channel_input = args.channel
    if not channel_input:
        channel_input = Prompt.ask(
            "[bold green]Enter channel username or link[/bold green] (e.g. @kalkastop or https://t.me/kalkastop)"
        )

    channel_input = channel_input.strip()
    if not channel_input:
        console.print("[bold red]Error:[/bold red] Channel username cannot be empty.")
        sys.exit(1)

    # Initialize SQLite Database
    db_path = config.export_dir / "telegram_archive.db"
    db = Database(db_path)
    db.connect()
    console.print(f"[dim]Initialized SQLite database at: {db_path}[/dim]")

    # Connect to Telegram MTProto
    session_file = config.session_name
    conn = TelegramConnection(
        api_id=config.api_id,
        api_hash=config.api_hash,
        session_path=Path(session_file),
    )

    console.print(f"[dim]Connecting to Telegram MTProto...[/dim]")
    client = await conn.connect()
    console.print("[bold green]✓ Authenticated with Telegram.[/bold green]\n")

    # Resolve target channel
    console.print(f"[dim]Resolving target channel '{channel_input}'...[/dim]")
    try:
        entity, channel_title, channel_username, total_count = await conn.resolve_channel(channel_input)
    except Exception as e:
        console.print(f"[bold red]Failed to resolve channel:[/bold red] {e}")
        db.close()
        await conn.disconnect()
        sys.exit(1)

    console.print(f"[bold green]✓ Channel found:[/bold green] [bold white]{channel_title}[/bold white] (@{channel_username})")
    if total_count is not None:
        console.print(f"[dim]Estimated available messages: {total_count}[/dim]\n")
    else:
        console.print("[dim]Total message count: unknown (live stream)[/dim]\n")

    console.print(f"[dim]Media download: {'ENABLED' if config.download_media else 'DISABLED'}[/dim]")
    console.print(f"[bold yellow]Video filter:[/bold yellow] download ONLY videos <= [bold green]{int(args.max_video_duration)}s[/bold green] (2 minutes)")
    console.print("[bold yellow]Audio/Docs filter:[/bold yellow] audio, voice, and documents [bold cyan]SKIPPED[/bold cyan] (metadata preserved in SQLite)")
    console.print(f"[dim]Export directory: {config.export_dir}[/dim]\n")

    # Initialize Progress UI
    progress_ui = ExporterProgressUI(
        channel_title=channel_title,
        channel_username=channel_username,
        total_estimated=total_count,
    )

    # Initialize Exporter
    exporter = ChannelExporter(
        client=client,
        entity=entity,
        channel_title=channel_title,
        channel_username=channel_username,
        export_dir=config.export_dir,
        db=db,
        download_media=config.download_media,
        max_video_duration=args.max_video_duration,
        progress_ui=progress_ui,
    )

    # Graceful shutdown handler
    loop = asyncio.get_running_loop()

    def handle_interrupt():
        console.print("\n[bold yellow]Interrupt signal received. Saving state and gracefully finishing...[/bold yellow]")
        exporter.stop_requested = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_interrupt)
        except NotImplementedError:
            pass

    # Run export
    progress_ui.start()
    try:
        await exporter.run()
    finally:
        progress_ui.stop()
        await conn.disconnect()

    # Collect final summary statistics from SQLite
    summary_stats = db.get_summary_stats(channel_username)

    # Run PRAGMA integrity_check
    integrity_ok, integrity_msgs = db.run_integrity_check()
    db.close()

    # Summary display
    progress_ui.print_summary(
        db_path=str(db_path),
        summary_stats=summary_stats,
        integrity_ok=integrity_ok,
        integrity_msgs=integrity_msgs,
    )


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[yellow]Process cancelled by user.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
