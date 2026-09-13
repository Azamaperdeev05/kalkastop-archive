"""Terminal UI and Progress reporting using Rich with video filtering metrics."""

import time
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

console = Console()


def format_elapsed(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS."""
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    rem_secs = secs % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{rem_secs:02d}"
    return f"{minutes:02d}:{rem_secs:02d}"


class ExporterProgressUI:
    """Rich live UI displaying progress and statistics matching user specifications."""

    def __init__(self, channel_title: str, channel_username: str, total_estimated: Optional[int] = None):
        self.channel_title = channel_title
        self.channel_username = channel_username
        self.total_estimated = total_estimated
        self.start_time = time.time()

        # Stats
        self.posts_processed = 0
        self.posts_saved = 0
        self.media_found = 0
        self.media_downloaded = 0
        self.photos_downloaded = 0
        self.short_videos_downloaded = 0
        self.long_videos_skipped = 0
        self.audio_skipped = 0
        self.documents_skipped = 0
        self.media_failed = 0
        self.current_message_id = 0
        self.status_message = "Starting..."

        self._live: Optional[Live] = None

    def start(self):
        """Start the live UI."""
        self._live = Live(self._generate_renderable(), console=console, refresh_per_second=4)
        self._live.start()

    def stop(self):
        """Stop the live UI."""
        if self._live:
            self._live.stop()
            self._live = None

    def update(
        self,
        posts_processed: Optional[int] = None,
        posts_saved: Optional[int] = None,
        media_found: Optional[int] = None,
        media_downloaded: Optional[int] = None,
        photos_downloaded: Optional[int] = None,
        short_videos_downloaded: Optional[int] = None,
        long_videos_skipped: Optional[int] = None,
        audio_skipped: Optional[int] = None,
        documents_skipped: Optional[int] = None,
        media_failed: Optional[int] = None,
        current_message_id: Optional[int] = None,
        status_message: Optional[str] = None,
    ):
        if posts_processed is not None:
            self.posts_processed = posts_processed
        if posts_saved is not None:
            self.posts_saved = posts_saved
        if media_found is not None:
            self.media_found = media_found
        if media_downloaded is not None:
            self.media_downloaded = media_downloaded
        if photos_downloaded is not None:
            self.photos_downloaded = photos_downloaded
        if short_videos_downloaded is not None:
            self.short_videos_downloaded = short_videos_downloaded
        if long_videos_skipped is not None:
            self.long_videos_skipped = long_videos_skipped
        if audio_skipped is not None:
            self.audio_skipped = audio_skipped
        if documents_skipped is not None:
            self.documents_skipped = documents_skipped
        if media_failed is not None:
            self.media_failed = media_failed
        if current_message_id is not None:
            self.current_message_id = current_message_id
        if status_message is not None:
            self.status_message = status_message

        if self._live:
            self._live.update(self._generate_renderable())

    def _generate_renderable(self) -> Panel:
        elapsed = time.time() - self.start_time

        table = Table(box=None, show_header=False, pad_edge=False)
        table.add_column("Key", style="bold cyan", width=28)
        table.add_column("Value", style="bold white")

        display_channel = f"@{self.channel_username}" if self.channel_username else self.channel_title
        table.add_row("Channel:", display_channel)
        table.add_row("Posts processed:", str(self.posts_processed))
        table.add_row("Posts saved in DB:", str(self.posts_saved))
        table.add_row("Photos downloaded:", f"[green]{self.photos_downloaded}[/green]")
        table.add_row("Videos <=120s downloaded:", f"[green]{self.short_videos_downloaded}[/green]")
        table.add_row("Videos >120s skipped:", f"[yellow]{self.long_videos_skipped}[/yellow]")
        table.add_row("Audio / voice skipped:", f"[cyan]{self.audio_skipped}[/cyan]")
        table.add_row("Documents skipped:", f"[cyan]{self.documents_skipped}[/cyan]")
        table.add_row(
            "Media failed:",
            f"[red]{self.media_failed}[/red]" if self.media_failed > 0 else "0",
        )
        table.add_row("Current message ID:", str(self.current_message_id) if self.current_message_id else "-")
        table.add_row("Elapsed time:", format_elapsed(elapsed))
        table.add_row("Status:", f"[dim]{self.status_message}[/dim]")

        # Progress bar
        pct_text = ""
        bar_len = 24
        if self.total_estimated and self.total_estimated > 0:
            ratio = min(1.0, self.posts_processed / self.total_estimated)
            filled = int(ratio * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            pct = int(ratio * 100)
            pct_text = f"[{bar}] {pct}% ({self.posts_processed}/{self.total_estimated})"
        else:
            filled = (self.posts_processed // 10) % bar_len
            bar = "░" * filled + "█" + "░" * (bar_len - filled - 1)
            pct_text = f"[{bar}] {self.posts_processed} messages processed"

        renderables = Table.grid(padding=1)
        renderables.add_row(table)
        renderables.add_row(Text.from_markup(f"\n[green]{pct_text}[/green]"))

        panel = Panel(
            renderables,
            title="[bold yellow]Telegram Channel Exporter (SQLite + Media Filter)[/bold yellow]",
            subtitle=f"[dim]{self.channel_title}[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
        return panel

    def print_summary(
        self,
        db_path: str,
        summary_stats: Dict[str, Any],
        integrity_ok: bool,
        integrity_msgs: list[str],
    ):
        """Prints the final summary report with exact requested statistics."""
        self.stop()

        display_channel = f"@{self.channel_username}" if self.channel_username else self.channel_title

        summary_table = Table(box=None, show_header=False, pad_edge=False)
        summary_table.add_column("Field", style="bold cyan", width=34)
        summary_table.add_column("Value", style="bold green")

        summary_table.add_row("Channel:", display_channel)
        summary_table.add_row("Total posts:", str(summary_stats.get("total_posts", self.posts_saved)))
        summary_table.add_row(
            "Photos downloaded:",
            f"[bold green]{summary_stats.get('photos_downloaded', self.photos_downloaded)}[/bold green]",
        )
        summary_table.add_row(
            "Videos <=120s downloaded:",
            f"[bold green]{summary_stats.get('short_videos_downloaded', self.short_videos_downloaded)}[/bold green]",
        )
        summary_table.add_row(
            "Videos >120s skipped:",
            f"[bold yellow]{summary_stats.get('long_videos_skipped', self.long_videos_skipped)}[/bold yellow]",
        )
        summary_table.add_row(
            "Audio skipped:",
            f"[bold cyan]{summary_stats.get('audio_skipped', self.audio_skipped)}[/bold cyan]",
        )
        summary_table.add_row(
            "Documents skipped:",
            f"[bold cyan]{summary_stats.get('documents_skipped', self.documents_skipped)}[/bold cyan]",
        )
        summary_table.add_row(
            "Download failures:",
            f"[red]{summary_stats.get('download_failures', self.media_failed)}[/red]"
            if summary_stats.get("download_failures", self.media_failed) > 0
            else "0",
        )
        summary_table.add_row(
            "Total disk usage:",
            f"[bold magenta]{summary_stats.get('total_disk_usage_mb', 0.0):.1f} MB[/bold magenta] "
            f"({summary_stats.get('total_disk_usage_gb', 0.0):.3f} GB)",
        )
        summary_table.add_row("Total elapsed:", format_elapsed(time.time() - self.start_time))
        summary_table.add_row("SQLite database:", f"[yellow]{db_path}[/yellow]")
        summary_table.add_row(
            "Integrity check:",
            "[bold green]OK (PASSED)[/bold green]" if integrity_ok else f"[bold red]FAILED: {', '.join(integrity_msgs)}[/bold red]",
        )

        panel = Panel(
            summary_table,
            title="[bold green]✓ Archive Export Summary[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        console.print()
        console.print(panel)
        console.print()
