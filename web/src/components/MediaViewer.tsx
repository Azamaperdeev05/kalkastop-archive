"use client";

import React, { useState } from "react";
import { Play, ExternalLink, Image as ImageIcon, Video, X, Clock, AlertCircle } from "lucide-react";
import { PostMedia } from "@/types/post";

interface MediaViewerProps {
  media?: PostMedia;
  postId: number;
  telegramUrl: string;
}

function formatDuration(seconds?: number | null): string {
  if (!seconds || seconds <= 0) return "";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function MediaViewer({ media, postId, telegramUrl }: MediaViewerProps) {
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [videoError, setVideoError] = useState(false);

  if (!media) return null;

  // Cloud CDN or local path resolution
  const cdnBase = process.env.NEXT_PUBLIC_MEDIA_URL || "";
  const mediaPath = media.path ? `${cdnBase}/${media.path}` : "";

  // 1. Photos
  if (media.type === "photo") {
    if (imageError) {
      return (
        <div className="my-3 flex items-center justify-between rounded-xl border border-dashed border-slate-300 bg-slate-50 p-3 text-xs text-slate-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400">
          <div className="flex items-center gap-2">
            <ImageIcon className="h-4 w-4 text-slate-400" />
            <span>Фотосурет Telegram каналында қолжетімді</span>
          </div>
          <a
            href={telegramUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-medium text-telegram hover:underline"
          >
            Көру <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      );
    }

    return (
      <div className="my-3">
        <div
          onClick={() => setImageModalOpen(true)}
          className="group relative cursor-zoom-in overflow-hidden rounded-2xl border border-slate-200/80 bg-slate-100 dark:border-zinc-800 dark:bg-zinc-900"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={mediaPath || `/media/images/${postId}.jpg`}
            alt={`Жазба #${postId} суреті`}
            loading="lazy"
            onError={() => setImageError(true)}
            className="max-h-[500px] w-full object-contain transition-transform duration-200 group-hover:scale-[1.01]"
          />
          <div className="pointer-events-none absolute bottom-2 right-2 rounded-lg bg-black/60 px-2 py-1 text-[11px] font-medium text-white backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity">
            Үлкейту
          </div>
        </div>

        {/* Fullscreen Lightbox Modal */}
        {imageModalOpen && (
          <div
            onClick={() => setImageModalOpen(false)}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 backdrop-blur-sm animate-in fade-in"
          >
            <button
              onClick={() => setImageModalOpen(false)}
              className="absolute top-4 right-4 rounded-full bg-white/10 p-2 text-white hover:bg-white/20 transition-colors"
              aria-label="Close image preview"
            >
              <X className="h-6 w-6" />
            </button>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={mediaPath || `/media/images/${postId}.jpg`}
              alt={`Жазба #${postId}`}
              className="max-h-[90vh] max-w-[95vw] rounded-lg object-contain shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}
      </div>
    );
  }

  // 2. Downloaded short videos (<= 120s)
  if (media.type === "video" && media.status === "downloaded") {
    if (videoError) {
      return (
        <div className="my-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-zinc-800 dark:bg-zinc-900/60">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-telegram/10 text-telegram">
                <Video className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800 dark:text-zinc-200">
                  Бейнежазба ({media.duration ? formatDuration(media.duration) : "< 2 мин"})
                </p>
                <p className="text-xs text-slate-500 dark:text-zinc-400">
                  Бейнені тікелей Telegram каналынан көруге болады
                </p>
              </div>
            </div>
            <a
              href={telegramUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-xl bg-telegram px-3 py-1.5 text-xs font-semibold text-white hover:bg-telegram-hover transition-colors shrink-0"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              Telegram-да көру
            </a>
          </div>
        </div>
      );
    }

    return (
      <div className="my-3">
        <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-black shadow-sm dark:border-zinc-800">
          <video
            controls
            preload="none"
            onError={() => setVideoError(true)}
            className="max-h-[500px] w-full bg-black object-contain"
          >
            <source src={mediaPath || `/media/videos/${postId}.mp4`} type="video/mp4" />
            Бейнені ойнату мүмкін емес.
          </video>
          {media.duration && (
            <div className="pointer-events-none absolute top-3 right-3 flex items-center gap-1 rounded-lg bg-black/70 px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm">
              <Clock className="h-3 w-3 text-amber-400" />
              <span>{formatDuration(media.duration)}</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 3. Skipped long videos (> 120s)
  if (media.type === "video" && media.status === "skipped_duration") {
    return (
      <div className="my-3 rounded-2xl border border-amber-200/80 bg-amber-50/70 p-3.5 dark:border-amber-900/40 dark:bg-amber-950/20">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs text-amber-900 dark:text-amber-300">
            <Clock className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <span>
              <strong>Ұзақ бейне ({formatDuration(media.duration)}):</strong> Архив көлемін үнемдеу мақсатында жүктелмеді
            </span>
          </div>
          <a
            href={telegramUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs font-semibold text-telegram hover:underline ml-auto"
          >
            Telegram-да толық көру <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    );
  }

  // 4. Skipped audio / voice
  if (media.status === "skipped_audio") {
    return (
      <div className="my-2 flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-400">
        <span>Аудио / Дауыстық хабарлама {media.duration ? `(${formatDuration(media.duration)})` : ""}</span>
        <a
          href={telegramUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 font-medium text-telegram hover:underline"
        >
          Тыңдау <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    );
  }

  // 5. Skipped documents
  if (media.status === "skipped_document") {
    return (
      <div className="my-2 flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-400">
        <span>Құжат файлы (PDF / Doc)</span>
        <a
          href={telegramUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 font-medium text-telegram hover:underline"
        >
          Telegram-нан ашу <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    );
  }

  return null;
}
