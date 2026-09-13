"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Header } from "@/components/Header";
import { FilterBar } from "@/components/FilterBar";
import { PostCard } from "@/components/PostCard";
import { Post, PostsApiResponse } from "@/types/post";
import { Loader2, ArrowUp, Frown, Sparkles, Send } from "lucide-react";

export default function HomePage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [totalFiltered, setTotalFiltered] = useState(0);
  const [totalChannelPosts, setTotalChannelPosts] = useState(4459);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [filterCounts, setFilterCounts] = useState({
    all: 4459,
    media: 1001,
    text: 3458,
    video: 40,
  });

  // Debounce search input by 300ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Track scroll position for "Back to top" button
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Fetch posts from API
  const fetchPosts = useCallback(
    async (targetPage: number, isNewFilter: boolean = false) => {
      if (isNewFilter) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      try {
        const params = new URLSearchParams({
          page: String(targetPage),
          limit: "25",
          filter: activeFilter,
          sort: sortOrder,
        });
        if (debouncedQuery) {
          params.set("q", debouncedQuery);
        }

        const res = await fetch(`/api/posts?${params.toString()}`);
        if (!res.ok) throw new Error("Failed to load posts");

        const data: PostsApiResponse = await res.json();

        if (isNewFilter || targetPage === 1) {
          setPosts(data.posts);
        } else {
          setPosts((prev) => [...prev, ...data.posts]);
        }

        setPage(data.page);
        setHasMore(data.hasMore);
        setTotalFiltered(data.total);
        if (data.filterCounts) {
          setFilterCounts(data.filterCounts);
          if (activeFilter === "all" && !debouncedQuery) {
            setTotalChannelPosts(data.total);
          }
        }
      } catch (err) {
        console.error("Error fetching posts:", err);
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [activeFilter, sortOrder, debouncedQuery]
  );

  // Re-fetch when filter, sort, or search changes
  useEffect(() => {
    fetchPosts(1, true);
  }, [fetchPosts]);

  const handleLoadMore = () => {
    if (!loadingMore && hasMore) {
      fetchPosts(page + 1, false);
    }
  };

  const handleSortToggle = () => {
    setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"));
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-zinc-950">
      <Header totalPosts={totalChannelPosts} />

      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-4 sm:py-6">
        {/* Controls: Search, Filter tabs, Sort */}
        <FilterBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          sortOrder={sortOrder}
          onSortToggle={handleSortToggle}
          filterCounts={filterCounts}
          totalFiltered={totalFiltered}
        />

        {/* Loading Spinner for new search/filter */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-zinc-500">
            <Loader2 className="h-8 w-8 animate-spin text-telegram mb-3" />
            <p className="text-sm font-medium">Жазбалар жүктелуде...</p>
          </div>
        ) : posts.length === 0 ? (
          /* Empty Search State */
          <div className="my-12 rounded-3xl border border-dashed border-slate-300 bg-white p-8 sm:p-12 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-zinc-800 dark:text-zinc-500">
              <Frown className="h-7 w-7" />
            </div>
            <h3 className="mt-4 text-base font-semibold text-slate-800 dark:text-white">
              Ешқандай жазба табылмады
            </h3>
            <p className="mt-1 text-sm text-slate-500 dark:text-zinc-400">
              Басқа сөз тіркесін немесе фильтрді қолданып көріңіз.
            </p>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-slate-100 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700 transition-colors"
              >
                Іздеуді тазалау
              </button>
            )}
          </div>
        ) : (
          /* Post Feed */
          <div className="space-y-4 pt-2">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}

            {/* Pagination / Load More */}
            <div className="pt-6 pb-10 text-center">
              {hasMore ? (
                <button
                  onClick={handleLoadMore}
                  disabled={loadingMore}
                  className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100 disabled:opacity-50 transition-all"
                >
                  {loadingMore ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Жүктелуде...</span>
                    </>
                  ) : (
                    <span>Тағы көрсету ({totalFiltered - posts.length} қалды)</span>
                  )}
                </button>
              ) : (
                <p className="text-xs font-medium text-slate-400 dark:text-zinc-600">
                  Барлық {totalFiltered.toLocaleString()} жазба көрсетілді
                </p>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Floating Scroll-to-Top Button */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          aria-label="Scroll to top"
          className="fixed bottom-6 right-6 z-40 flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-lg hover:bg-slate-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100 transition-all animate-in fade-in"
        >
          <ArrowUp className="h-5 w-5" />
        </button>
      )}

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200/80 bg-white py-6 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto max-w-4xl px-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 dark:text-zinc-400">
          <p>
            «Калькасыз қазақ тілі» (@kalkastop) жазбаларының веб-архиві. Авторы — Назгүл Қожабек.
          </p>
          <a
            href="https://t.me/kalkastop"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-semibold text-telegram hover:underline"
          >
            <Send className="h-3 w-3" />
            t.me/kalkastop
          </a>
        </div>
      </footer>
    </div>
  );
}
