"use client";

import React from "react";
import { Search, X, Image as ImageIcon, FileText, Video, Layers, ArrowUpDown } from "lucide-react";

interface FilterCounts {
  all: number;
  media: number;
  text: number;
  video: number;
}

interface FilterBarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  activeFilter: string;
  onFilterChange: (filter: string) => void;
  sortOrder: "desc" | "asc";
  onSortToggle: () => void;
  filterCounts: FilterCounts;
  totalFiltered: number;
}

export function FilterBar({
  searchQuery,
  onSearchChange,
  activeFilter,
  onFilterChange,
  sortOrder,
  onSortToggle,
  filterCounts,
  totalFiltered,
}: FilterBarProps) {
  const filters = [
    { id: "all", label: "Барлығы", icon: Layers, count: filterCounts.all },
    { id: "media", label: "Медиамен", icon: ImageIcon, count: filterCounts.media },
    { id: "text", label: "Мәтін", icon: FileText, count: filterCounts.text },
    { id: "video", label: "Бейне", icon: Video, count: filterCounts.video },
  ];

  return (
    <div className="space-y-3 pb-2 pt-4">
      {/* Search Bar */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 dark:text-zinc-500">
          <Search className="h-4 w-4" />
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Жазбалардан іздеу (мысалы: калька, етістік, сөздік)..."
          className="w-full rounded-2xl border border-slate-200 bg-white py-2.5 pl-10 pr-10 text-sm text-slate-900 placeholder:text-slate-400 shadow-sm focus:border-telegram focus:outline-none focus:ring-2 focus:ring-telegram/20 dark:border-zinc-800 dark:bg-zinc-900 dark:text-white dark:placeholder:text-zinc-500 transition-all"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange("")}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600 dark:hover:text-zinc-200"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Filter Tabs & Sort Button */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          {filters.map((f) => {
            const Icon = f.icon;
            const isActive = activeFilter === f.id;
            return (
              <button
                key={f.id}
                onClick={() => onFilterChange(f.id)}
                className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs sm:text-sm font-medium transition-all ${
                  isActive
                    ? "bg-slate-900 text-white shadow-sm dark:bg-white dark:text-zinc-900"
                    : "bg-white text-slate-600 border border-slate-200/80 hover:bg-slate-100 hover:text-slate-900 dark:bg-zinc-900 dark:text-zinc-400 dark:border-zinc-800 dark:hover:bg-zinc-800 dark:hover:text-white"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{f.label}</span>
                <span
                  className={`ml-0.5 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                    isActive
                      ? "bg-white/20 text-white dark:bg-zinc-900/20 dark:text-zinc-900"
                      : "bg-slate-200/80 text-slate-800 dark:bg-zinc-800 dark:text-zinc-200"
                  }`}
                >
                  {f.count.toLocaleString()}
                </span>
              </button>
            );
          })}
        </div>

        {/* Sort order toggle */}
        <button
          onClick={onSortToggle}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200/80 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 transition-colors shrink-0"
          title="Сұрыптау ретін өзгерту"
        >
          <ArrowUpDown className="h-3.5 w-3.5" />
          <span>{sortOrder === "desc" ? "Жаңалары алдымен" : "Ескілері алдымен"}</span>
        </button>
      </div>

      {/* Active search results counter notice */}
      {searchQuery && (
        <p className="text-xs text-slate-500 dark:text-zinc-400">
          «<strong className="text-slate-800 dark:text-zinc-200">{searchQuery}</strong>» сұранысы бойынша{" "}
          <strong className="text-slate-800 dark:text-zinc-200">{totalFiltered.toLocaleString()}</strong> жазба табылды
        </p>
      )}
    </div>
  );
}
