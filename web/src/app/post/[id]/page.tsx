import React from "react";
import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import { ArrowLeft, ChevronLeft, ChevronRight, Eye, Calendar, BookOpen, Share2 } from "lucide-react";
import rawPosts from "@/data/posts.json";
import { Post } from "@/types/post";
import { MediaViewer } from "@/components/MediaViewer";
import { ShareButtons } from "@/components/ShareButtons";

const allPosts = rawPosts as Post[];
const baseUrl = "https://web-tau-ten-13.vercel.app";

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

function cleanSnippet(text: string, maxLength: number): string {
  if (!text) return "";
  const cleaned = text
    .replace(/https?:\/\/[^\s]+/g, "")
    .replace(/\s+/g, " ")
    .trim();
  if (cleaned.length <= maxLength) return cleaned;
  return cleaned.slice(0, maxLength).trim() + "...";
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export const dynamicParams = true;

// Pre-render top 150 most recent posts for instant static delivery
export async function generateStaticParams() {
  return allPosts.slice(0, 150).map((post) => ({
    id: String(post.id),
  }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const postId = Number(id);
  const post = allPosts.find((p) => p.id === postId);

  if (!post) {
    return {
      title: "Жазба табылмады",
      description: "Іздеген жазбаңыз архивте табылмады.",
    };
  }

  const snippet = cleanSnippet(post.text, 120) || `Жазба #${post.id}`;
  const description =
    cleanSnippet(post.text, 160) ||
    `Назгүл Қожабектің 'Калькасыз қазақ тілі' Telegram-арнасындағы #${post.id} жазбасы.`;

  const pageUrl = `${baseUrl}/post/${post.id}`;
  const imageUrl =
    post.media?.type === "photo"
      ? `${baseUrl}/media/images/${post.id}.jpg`
      : undefined;

  return {
    title: `${snippet} (#${post.id})`,
    description,
    alternates: {
      canonical: pageUrl,
      languages: {
        "kk-KZ": pageUrl,
        kk: pageUrl,
        "x-default": pageUrl,
      },
    },
    openGraph: {
      title: `${snippet} (#${post.id}) | Калькасыз қазақ тілі`,
      description,
      url: pageUrl,
      type: "article",
      publishedTime: post.date,
      authors: ["Назгүл Қожабек"],
      images: imageUrl ? [{ url: imageUrl, alt: `Жазба #${post.id}` }] : undefined,
    },
    twitter: {
      card: imageUrl ? "summary_large_image" : "summary",
      title: `${snippet} (#${post.id})`,
      description,
      images: imageUrl ? [imageUrl] : undefined,
    },
    other: {
      "geo.region": "KZ",
      "geo.placename": "Kazakhstan",
      "content-language": "kk",
    },
  };
}

export default async function PostDetailPage({ params }: PageProps) {
  const { id } = await params;
  const postId = Number(id);
  const postIndex = allPosts.findIndex((p) => p.id === postId);

  if (postIndex === -1) {
    notFound();
  }

  const post = allPosts[postIndex];
  const nextPost = postIndex > 0 ? allPosts[postIndex - 1] : null; // newer
  const prevPost = postIndex < allPosts.length - 1 ? allPosts[postIndex + 1] : null; // older

  const snippet = cleanSnippet(post.text, 100) || `Жазба #${post.id}`;
  const pageUrl = `${baseUrl}/post/${post.id}`;

  // Structured Data (JSON-LD) for SEO / AI Search (GEO)
  const structuredDataPosting = {
    "@context": "https://schema.org",
    "@type": "SocialMediaPosting",
    "@id": `${pageUrl}#posting`,
    headline: snippet,
    articleBody: post.text,
    datePublished: post.date,
    url: pageUrl,
    inLanguage: "kk-KZ",
    author: {
      "@type": "Person",
      name: "Назгүл Қожабек",
      jobTitle: "Журналист, тіл жанашыры",
      url: "https://t.me/kalkastop",
    },
    publisher: {
      "@type": "Organization",
      name: "Калькасыз қазақ тілі (@kalkastop)",
      url: baseUrl,
    },
    interactionStatistic: [
      {
        "@type": "InteractionCounter",
        interactionType: "https://schema.org/ViewAction",
        userInteractionCount: post.views,
      },
    ],
    mainEntityOfPage: pageUrl,
  };

  const breadcrumbsData = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: "Басты бет",
        item: baseUrl,
      },
      {
        "@type": "ListItem",
        position: 2,
        name: `Жазба #${post.id}`,
        item: pageUrl,
      },
    ],
  };

  const lines = post.text ? post.text.split("\n") : [];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 antialiased dark:bg-zinc-950 dark:text-zinc-100">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredDataPosting) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbsData) }}
      />

      {/* Top Header */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/80 backdrop-blur-md dark:border-zinc-800 dark:bg-zinc-900/80">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3 sm:px-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-telegram dark:text-zinc-400 dark:hover:text-telegram transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Барлық жазбаларға оралу</span>
          </Link>

          <Link
            href="/"
            className="flex items-center gap-2 font-bold text-slate-900 dark:text-white"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-telegram text-white">
              <BookOpen className="h-4 w-4" />
            </div>
            <span className="hidden sm:inline text-sm">Калькасыз қазақ тілі</span>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
        {/* Breadcrumb Navigation */}
        <nav aria-label="Нан қиқымы" className="mb-4 text-xs text-slate-500 dark:text-zinc-400">
          <ol className="flex items-center gap-1.5">
            <li>
              <Link href="/" className="hover:text-telegram transition-colors">
                Басты бет
              </Link>
            </li>
            <li>/</li>
            <li className="font-semibold text-slate-700 dark:text-zinc-300">
              Жазба #{post.id}
            </li>
          </ol>
        </nav>

        {/* Post Card */}
        <article className="rounded-3xl border border-slate-200/90 bg-white p-5 sm:p-7 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          {/* Post Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4 dark:border-zinc-800">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center rounded-xl bg-telegram/10 px-2.5 py-1 text-sm font-bold text-telegram">
                #{post.id}
              </span>
              <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-zinc-400">
                <Calendar className="h-3.5 w-3.5" />
                <time dateTime={post.date}>{formatKazakhDate(post.date)}</time>
              </div>
            </div>

            {post.views > 0 && (
              <div
                className="inline-flex items-center gap-1.5 text-xs text-slate-400 dark:text-zinc-500"
                title="Көрілім саны"
              >
                <Eye className="h-4 w-4" />
                <span>{post.views.toLocaleString()} көрілім</span>
              </div>
            )}
          </div>

          {/* Media Content */}
          <div className="my-4">
            <MediaViewer media={post.media} postId={post.id} telegramUrl={post.url} priority={true} />
          </div>

          {/* Post Text */}
          <div className="space-y-3 text-base sm:text-lg leading-relaxed text-slate-800 dark:text-zinc-200 break-words whitespace-pre-wrap">
            {lines.map((line, idx) => {
              if (!line.trim()) {
                return <div key={idx} className="h-3" />;
              }

              const words = line.split(" ");
              return (
                <p key={idx} className="leading-relaxed">
                  {words.map((word, wIdx) => {
                    if (word.startsWith("http://") || word.startsWith("https://")) {
                      return (
                        <React.Fragment key={wIdx}>
                          <a
                            href={word}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-telegram-text dark:text-telegram-darkText hover:underline font-semibold break-all"
                          >
                            {word}
                          </a>{" "}
                        </React.Fragment>
                      );
                    }
                    if (word.startsWith("#") && word.length > 1) {
                      return (
                        <React.Fragment key={wIdx}>
                          <span className="text-telegram-text dark:text-telegram-darkText font-semibold">{word}</span>{" "}
                        </React.Fragment>
                      );
                    }
                    return word + " ";
                  })}
                </p>
              );
            })}
          </div>

          {/* Share & External Actions */}
          <div className="mt-6">
            <ShareButtons
              url={pageUrl}
              telegramUrl={post.url}
              title={`Калькасыз қазақ тілі #${post.id}: ${snippet}`}
              postId={post.id}
            />
          </div>
        </article>

        {/* Adjacent Posts Navigation (Pagination) */}
        <nav aria-label="Жазбалар бойынша шарлау" className="mt-6 grid grid-cols-2 gap-3">
          {prevPost ? (
            <Link
              href={`/post/${prevPost.id}`}
              className="flex flex-col gap-1 rounded-2xl border border-slate-200/80 bg-white p-3.5 sm:p-4 text-left hover:border-telegram/40 hover:bg-slate-50/50 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:bg-zinc-850 transition-all"
            >
              <div className="flex items-center gap-1 text-xs text-slate-400 dark:text-zinc-500">
                <ChevronLeft className="h-3.5 w-3.5" />
                <span>Алдыңғы жазба</span>
              </div>
              <span className="text-sm font-semibold text-slate-800 dark:text-zinc-200 line-clamp-1">
                #{prevPost.id} {cleanSnippet(prevPost.text, 40)}
              </span>
            </Link>
          ) : (
            <div />
          )}

          {nextPost ? (
            <Link
              href={`/post/${nextPost.id}`}
              className="flex flex-col gap-1 rounded-2xl border border-slate-200/80 bg-white p-3.5 sm:p-4 text-right hover:border-telegram/40 hover:bg-slate-50/50 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:bg-zinc-850 transition-all ml-auto w-full"
            >
              <div className="flex items-center justify-end gap-1 text-xs text-slate-400 dark:text-zinc-500">
                <span>Келесі жазба</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </div>
              <span className="text-sm font-semibold text-slate-800 dark:text-zinc-200 line-clamp-1">
                #{nextPost.id} {cleanSnippet(nextPost.text, 40)}
              </span>
            </Link>
          ) : (
            <div />
          )}
        </nav>
      </main>
    </div>
  );
}
