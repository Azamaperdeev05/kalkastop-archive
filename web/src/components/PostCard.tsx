"use client";

import React, { useState } from "react";
import { Eye, Share2, ExternalLink, Check, Copy } from "lucide-react";
import { Post } from "@/types/post";
import { MediaViewer } from "./MediaViewer";

interface PostCardProps {
  post: Post;
}

const KAZAKH_MONTHS = [
  "қаңтар",
  "ақпан",
  "наурыз",
  "сәуір",
  "мамыр",
  "маусым",
  "шілде",
  "тамыз",
  "қыркүйек",
  "қазан",
  "қараша",
  "желтоқсан",
];

function formatKazakhDate(isoDateStr: string): string {
  if (!isoDateStr) return "";
  try {
    const d = new Date(isoDateStr);
    const day = d.getDate();
    const month = KAZAKH_MONTHS[d.getMonth()];
    const year = d.getFullYear();
    const hours = d.getHours().toString().padStart(2, "0");
    const minutes = d.getMinutes().toString().padStart(2, "0");
    return `${day} ${month} ${year}, ${hours}:${minutes}`;
  } catch {
    return isoDateStr;
  }
}

function renderFormattedText(text: string) {
  if (!text) return null;

  // Split lines while preserving paragraphs
  const lines = text.split("\n");

  return (
    <div className="space-y-1.5 text-sm sm:text-base leading-relaxed text-slate-800 dark:text-zinc-200 break-words whitespace-pre-wrap">
      {lines.map((line, idx) => {
        if (!line.trim()) {
          return <div key={idx} className="h-2" />;
        }

        // Tokenize line for URLs and hashtags
        const words = line.split(" ");
        return (
          <p key={idx} className="leading-relaxed">
            {words.map((word, wIdx) => {
              // URL detection
              if (word.startsWith("http://") || word.startsWith("https://")) {
                return (
                  <React.Fragment key={wIdx}>
                    <a
                      href={word}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-telegram hover:underline font-medium break-all"
                    >
                      {word}
                    </a>{" "}
                  </React.Fragment>
                );
              }
              // Hashtag detection
              if (word.startsWith("#") && word.length > 1) {
                return (
                  <React.Fragment key={wIdx}>
                    <span className="text-telegram font-medium">{word}</span>{" "}
                  </React.Fragment>
                );
              }
              return word + " ";
            })}
          </p>
        );
      })}
    </div>
  );
}

export function PostCard({ post }: PostCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(post.url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <article className="group rounded-2xl border border-slate-200/80 bg-white p-4 sm:p-5 shadow-sm transition-all hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900">
      {/* Post Metadata Header */}
      <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-3 dark:border-zinc-800/80">
        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-zinc-400">
          <span className="font-semibold text-telegram">#{post.id}</span>
          <span>•</span>
          <time dateTime={post.date}>{formatKazakhDate(post.date)}</time>
        </div>

        <div className="flex items-center gap-2">
          {post.views > 0 && (
            <div
              className="inline-flex items-center gap-1 text-xs text-slate-400 dark:text-zinc-500"
              title="Көрілім саны"
            >
              <Eye className="h-3.5 w-3.5" />
              <span>{post.views.toLocaleString()}</span>
            </div>
          )}

          {/* Copy link button */}
          <button
            onClick={handleCopyLink}
            title="Сілтемені көшіру"
            className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
          </button>

          {/* Original Telegram link */}
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            title="Telegram-нан ашу"
            className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-telegram hover:bg-telegram/10 transition-colors"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>

      {/* Media Content */}
      <MediaViewer media={post.media} postId={post.id} telegramUrl={post.url} />

      {/* Post Text */}
      <div className="mt-3">{renderFormattedText(post.text)}</div>
    </article>
  );
}
