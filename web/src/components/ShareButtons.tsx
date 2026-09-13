"use client";

import React, { useState } from "react";
import { Check, Copy, Share2, ExternalLink, MessageCircle, Send } from "lucide-react";

interface ShareButtonsProps {
  url: string;
  telegramUrl: string;
  title: string;
  postId: number;
}

export function ShareButtons({ url, telegramUrl, title, postId }: ShareButtonsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const encodedUrl = encodeURIComponent(url);
  const encodedText = encodeURIComponent(`${title}\n\n`);
  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodedText}${encodedUrl}`;
  const telegramShareUrl = `https://t.me/share/url?url=${encodedUrl}&text=${encodeURIComponent(title)}`;

  return (
    <div className="flex flex-wrap items-center gap-2 pt-4 border-t border-slate-100 dark:border-zinc-800">
      {/* Copy link */}
      <button
        onClick={handleCopy}
        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-750 transition-colors"
      >
        {copied ? (
          <>
            <Check className="h-3.5 w-3.5 text-emerald-500" />
            <span>Көшірілді!</span>
          </>
        ) : (
          <>
            <Copy className="h-3.5 w-3.5 text-slate-500 dark:text-zinc-400" />
            <span>Сілтемені көшіру</span>
          </>
        )}
      </button>

      {/* WhatsApp */}
      <a
        href={whatsappUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50/70 px-3 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-100 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300 dark:hover:bg-emerald-900/40 transition-colors"
      >
        <MessageCircle className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
        <span>WhatsApp</span>
      </a>

      {/* Telegram */}
      <a
        href={telegramShareUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 rounded-xl border border-sky-200 bg-sky-50/70 px-3 py-1.5 text-xs font-medium text-sky-700 hover:bg-sky-100 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-300 dark:hover:bg-sky-900/40 transition-colors"
      >
        <Send className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
        <span>Telegram</span>
      </a>

      {/* Original Telegram post */}
      <a
        href={telegramUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-telegram hover:bg-telegram/10 dark:border-zinc-800 dark:bg-zinc-900 ml-auto transition-colors"
      >
        <span>Telegram-да ашу</span>
        <ExternalLink className="h-3.5 w-3.5" />
      </a>
    </div>
  );
}
