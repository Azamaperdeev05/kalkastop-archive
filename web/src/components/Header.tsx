"use client";

import React, { useEffect, useState } from "react";
import { Send, Moon, Sun, BookOpen, Sparkles } from "lucide-react";

interface HeaderProps {
  totalPosts: number;
}

export function Header({ totalPosts }: HeaderProps) {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check local storage or system preference
    const stored = localStorage.getItem("theme");
    if (stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      setIsDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    if (isDark) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
      setIsDark(false);
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
      setIsDark(true);
    }
  };

  return (
    <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-md dark:border-zinc-800/80 dark:bg-zinc-900/90 sticky top-0 z-30 transition-colors">
      <div className="mx-auto max-w-4xl px-4 py-3 sm:py-4">
        <div className="flex items-center justify-between gap-3">
          {/* Channel branding */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-telegram text-white shadow-sm shadow-telegram/30">
              <BookOpen className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="truncate text-base sm:text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                  Калькасыз қазақ тілі
                </h1>
                <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-zinc-800 dark:text-zinc-400">
                  <Sparkles className="h-3 w-3 text-amber-500" />
                  Архив
                </span>
              </div>
              <p className="truncate text-xs sm:text-sm text-slate-500 dark:text-zinc-400">
                <a
                  href="https://t.me/kalkastop"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-telegram hover:underline"
                >
                  @kalkastop
                </a>
                <span className="mx-1.5 opacity-40">•</span>
                <span>Назгүл Қожабек</span>
                {totalPosts > 0 && (
                  <>
                    <span className="mx-1.5 opacity-40">•</span>
                    <span>{totalPosts.toLocaleString()} жазба</span>
                  </>
                )}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-800 transition-colors"
            >
              {isDark ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
            </button>

            <a
              href="https://t.me/kalkastop"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-xl bg-telegram px-3 py-2 text-xs sm:text-sm font-semibold text-white shadow-sm hover:bg-telegram-hover transition-colors"
            >
              <Send className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Каналға өту</span>
              <span className="sm:hidden">Telegram</span>
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}
