import rawPosts from "@/data/posts.json";
import { Post } from "@/types/post";
import { HomeClient } from "@/components/HomeClient";

const allPosts = rawPosts as Post[];
const initialPosts = allPosts.slice(0, 25);
const totalCount = allPosts.length;

const initialFilterCounts = {
  all: totalCount,
  media: allPosts.filter((p) => p.has_media).length,
  text: allPosts.filter((p) => !p.has_media).length,
  video: allPosts.filter((p) => p.media?.type === "video").length,
};

export default function HomePage() {
  return (
    <HomeClient
      initialPosts={initialPosts}
      totalCount={totalCount}
      initialFilterCounts={initialFilterCounts}
    />
  );
}
