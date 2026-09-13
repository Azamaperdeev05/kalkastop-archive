# Telegram Channel Archive & Web Viewer (@kalkastop)

A high-performance local Telegram channel exporter and public web archive viewer for **@kalkastop** ("Калькасыз қазақ тілі. Назгүл Қожабек").

- 🌐 **Live Web Viewer**: [https://web-tau-ten-13.vercel.app](https://web-tau-ten-13.vercel.app)
- 📦 **GitHub Repository**: [https://github.com/Azamaperdeev05/kalkastop-archive](https://github.com/Azamaperdeev05/kalkastop-archive)
- 📱 **Telegram Channel**: [@kalkastop](https://t.me/kalkastop)

---

## 🏗️ Architecture Overview

The system consists of two primary components:

1. **Python Exporter & Archive (`/`)**:
   - Uses Telegram MTProto API via **Telethon** with native `cryptg` encryption.
   - Extracts complete post history and stores it in an indexed, WAL-enabled **SQLite database** (`export/telegram_archive.db`).
   - Applies an automated **video duration filter**: only downloads short videos ($\le 120$ seconds); long videos ($> 120$s), audio, and documents are cleanly recorded with status `skipped_*` and metadata preserved in SQLite.
   - Idempotent and resumable.

2. **Public Web Viewer (`web/`)**:
   - Modern, minimalist, mobile-first **Next.js 15** application with **Tailwind CSS**.
   - Read-only data architecture: pre-compiled from SQLite into optimized JSON (`web/src/data/posts.json`), served in paginated chunks via `/api/posts`.
   - In-memory instant search supporting Kazakh Cyrillic (`ә, і, ң, ғ, ү, ұ, қ, ө, һ`) and Russian characters.
   - Filter pills: **Барлығы** (All), **Медиамен** (With media), **Мәтін** (Text only), **Бейне** (Videos).
   - Media viewer with image lightbox, video player with duration badge, and graceful Telegram fallback cards.
   - Light/Dark mode support.
   - Production-ready for **Vercel** deployment.

---

## 📁 Repository Structure

```
├── app.py                      # Python Telegram exporter CLI entrypoint
├── config.py                   # Configuration and credential loader
├── database.py                 # SQLite database manager (posts & media tables)
├── exporter.py                 # Core scraping, duration filtering, and download logic
├── models.py                   # Data models (Post, MediaItem)
├── progress.py                 # Terminal progress UI (Rich)
├── telegram_client.py          # MTProto client connector
├── scripts/
│   └── export_web_data.py      # SQLite to Web data sync and image export
├── tests/                      # Automated test suite (29 tests)
├── export/                     # (Git-ignored) Local SQLite archive & media
│   ├── telegram_archive.db
│   └── media/
│       ├── images/             # 961 downloaded photos
│       └── videos/             # 40 downloaded short videos (<=120s)
└── web/                        # Next.js public web viewer
    ├── package.json
    ├── public/
    │   └── media/images/       # 961 photos deployed to Vercel CDN
    └── src/
        ├── app/
        │   ├── api/posts/      # Paginated search/filter API
        │   ├── layout.tsx
        │   └── page.tsx        # Main feed UI
        ├── components/
        │   ├── FilterBar.tsx
        │   ├── Header.tsx
        │   ├── MediaViewer.tsx
        │   └── PostCard.tsx
        ├── data/
        │   └── posts.json      # 4,459 posts extracted from SQLite
        └── types/
```

---

## 🚀 Local Development

### 1. Python Exporter (Data Fetching)

```bash
# Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run automated test suite
PYTHONPATH=. ./.venv/bin/python -m pytest tests/ -v

# Run exporter for @kalkastop
python app.py --channel @kalkastop
```

### 2. Sync SQLite to Web

```bash
python3 scripts/export_web_data.py
```

### 3. Run Web Viewer

```bash
cd web
npm install
npm run dev
# Open http://localhost:3000
```

---

## ☁️ Media Architecture & Deployment

### Photos (55 MB)
- 961 images are stored in `web/public/media/images/`.
- Deployed directly with the web application and cached globally on Vercel's Edge CDN.

### Videos (716 MB)
- 40 short videos ($\le 120$ seconds) are stored locally in `export/media/videos/`.
- To prevent repository bloat and exceed Git/Vercel size limits, raw `.mp4` video files are excluded from Git.
- **Local Dev**: Videos play directly from local media.
- **Production**:
  - Configurable via `NEXT_PUBLIC_MEDIA_URL` (pointing to Vercel Blob or an S3/R2 bucket).
  - Fallback: Any video not yet uploaded displays an interactive card with exact duration and a direct "Watch on Telegram" button linking to `t.me/kalkastop/{id}`.

---

## 🔒 Security

- `.env`, `*.session`, and SQLite databases are strictly ignored by `.gitignore`.
- No credentials or API hashes are exposed in public code, bundles, or Git history.
