import { NextRequest, NextResponse } from "next/server";
import rawPosts from "@/data/posts.json";
import { Post, PostsApiResponse } from "@/types/post";

const allPosts: Post[] = rawPosts as Post[];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const page = Math.max(1, parseInt(searchParams.get("page") || "1", 10));
  const limit = Math.min(100, Math.max(5, parseInt(searchParams.get("limit") || "25", 10)));
  const filter = (searchParams.get("filter") || "all").toLowerCase();
  const sort = (searchParams.get("sort") || "desc").toLowerCase();
  const q = (searchParams.get("q") || "").trim().toLowerCase();

  // 1. Text Search Filter
  let searched = allPosts;
  if (q) {
    searched = allPosts.filter((post) => {
      if (String(post.id) === q) return true;
      return post.text.toLowerCase().includes(q);
    });
  }

  // 2. Compute filter counts based on current search query
  const filterCounts = {
    all: searched.length,
    media: searched.filter((p) => p.has_media).length,
    text: searched.filter((p) => !p.has_media).length,
    video: searched.filter((p) => p.media?.type === "video").length,
  };

  // 3. Category Filter
  let filtered = searched;
  if (filter === "media") {
    filtered = searched.filter((p) => p.has_media);
  } else if (filter === "text") {
    filtered = searched.filter((p) => !p.has_media);
  } else if (filter === "video") {
    filtered = searched.filter((p) => p.media?.type === "video");
  }

  // 4. Sort
  const sorted = [...filtered].sort((a, b) => {
    return sort === "asc" ? a.id - b.id : b.id - a.id;
  });

  // 5. Pagination
  const total = sorted.length;
  const totalPages = Math.ceil(total / limit);
  const startIndex = (page - 1) * limit;
  const paginated = sorted.slice(startIndex, startIndex + limit);
  const hasMore = page < totalPages;

  const responseData: PostsApiResponse = {
    posts: paginated,
    total,
    page,
    limit,
    totalPages,
    hasMore,
    filterCounts,
  };

  return NextResponse.json(responseData, {
    headers: {
      "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
    },
  });
}
