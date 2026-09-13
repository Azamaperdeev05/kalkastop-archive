import type { MetadataRoute } from "next";
import rawPosts from "@/data/posts.json";
import { Post } from "@/types/post";

const allPosts = rawPosts as Post[];
const baseUrl = "https://web-tau-ten-13.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const postUrls: MetadataRoute.Sitemap = allPosts.map((post) => {
    let date = new Date();
    if (post.date) {
      const parsed = new Date(post.date);
      if (!isNaN(parsed.getTime())) {
        date = parsed;
      }
    }

    return {
      url: `${baseUrl}/post/${post.id}`,
      lastModified: date,
      changeFrequency: "monthly" as const,
      priority: 0.8,
    };
  });

  return [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: "daily" as const,
      priority: 1.0,
    },
    ...postUrls,
  ];
}
