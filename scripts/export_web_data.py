"""Export SQLite telegram archive data into optimized JSON and copy images for the web app."""

import os
import json
import shutil
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "export" / "telegram_archive.db"
MEDIA_DIR = ROOT_DIR / "export" / "media"
WEB_DIR = ROOT_DIR / "web"
WEB_DATA_DIR = WEB_DIR / "src" / "data"
WEB_PUBLIC_MEDIA = WEB_DIR / "public" / "media"


def export_data():
    print(f"Connecting to database: {DB_PATH}")
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            message_id,
            channel,
            date,
            text,
            views,
            forwards,
            replies,
            url,
            has_media,
            media_type,
            media_path,
            media_status,
            duration_seconds,
            grouped_id
        FROM posts
        ORDER BY message_id DESC;
    """)
    rows = cursor.fetchall()

    posts = []
    stats = {
        "total_posts": len(rows),
        "photos": 0,
        "videos": 0,
        "videos_skipped": 0,
        "audio_skipped": 0,
        "docs_skipped": 0,
        "other": 0,
    }

    for r in rows:
        post = {
            "id": r["message_id"],
            "channel": r["channel"] or "kalkastop",
            "date": r["date"],
            "text": r["text"] or "",
            "views": r["views"] or 0,
            "forwards": r["forwards"] or 0,
            "replies": r["replies"],
            "url": r["url"] or f"https://t.me/kalkastop/{r['message_id']}",
            "has_media": bool(r["has_media"]),
            "grouped_id": r["grouped_id"],
        }

        media_type = r["media_type"]
        media_status = r["media_status"]
        media_path = r["media_path"]
        duration = r["duration_seconds"]

        if r["has_media"]:
            if media_type == "photo" and media_status == "downloaded":
                stats["photos"] += 1
                post["media"] = {
                    "type": "photo",
                    "status": "downloaded",
                    "path": media_path,  # e.g. media/images/10.jpg
                }
            elif media_type in ("video", "round_video"):
                if media_status == "downloaded":
                    stats["videos"] += 1
                    post["media"] = {
                        "type": "video",
                        "status": "downloaded",
                        "path": media_path,  # e.g. media/videos/49.mp4
                        "duration": duration,
                    }
                else:
                    stats["videos_skipped"] += 1
                    post["media"] = {
                        "type": "video",
                        "status": "skipped_duration",
                        "duration": duration,
                    }
            elif media_type in ("audio", "voice"):
                stats["audio_skipped"] += 1
                post["media"] = {
                    "type": "audio",
                    "status": "skipped_audio",
                    "duration": duration,
                }
            elif media_type == "document":
                stats["docs_skipped"] += 1
                post["media"] = {
                    "type": "document",
                    "status": "skipped_document",
                }
            else:
                stats["other"] += 1
                post["media"] = {
                    "type": media_type or "other",
                    "status": media_status or "skipped",
                }

        posts.append(post)

    conn.close()

    # Create destination directories
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    images_dest = WEB_PUBLIC_MEDIA / "images"
    images_dest.mkdir(parents=True, exist_ok=True)

    # Write posts.json
    out_file = WEB_DATA_DIR / "posts.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=None)

    file_size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"✓ Wrote {len(posts)} posts to {out_file} ({file_size_mb:.2f} MB)")
    print(f"  Stats: {stats}")

    # Copy images to web/public/media/images
    images_src = MEDIA_DIR / "images"
    if images_src.exists():
        copied = 0
        for img in images_src.iterdir():
            if img.is_file():
                dest = images_dest / img.name
                if not dest.exists() or dest.stat().st_size != img.stat().st_size:
                    shutil.copy2(img, dest)
                copied += 1
        print(f"✓ Synced {copied} photos to {images_dest}")

    # For local dev videos, create web/public/media/videos directory or symlink
    videos_src = MEDIA_DIR / "videos"
    videos_dest = WEB_PUBLIC_MEDIA / "videos"
    videos_dest.mkdir(parents=True, exist_ok=True)
    if videos_src.exists():
        linked = 0
        for vid in videos_src.iterdir():
            if vid.is_file():
                dest = videos_dest / vid.name
                if not dest.exists():
                    try:
                        dest.symlink_to(vid.resolve())
                        linked += 1
                    except OSError:
                        shutil.copy2(vid, dest)
                        linked += 1
        print(f"✓ Linked/copied {linked} local short videos to {videos_dest}")

    print("Data export and media sync completed successfully!")


if __name__ == "__main__":
    export_data()
