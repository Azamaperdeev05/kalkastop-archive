export interface PostMedia {
  type: string;
  status: string;
  path?: string;
  duration?: number | null;
}

export interface Post {
  id: number;
  channel: string;
  date: string;
  text: string;
  views: number;
  forwards: number;
  replies: number | null;
  url: string;
  has_media: boolean;
  grouped_id: number | null;
  media?: PostMedia;
}

export interface PostsApiResponse {
  posts: Post[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasMore: boolean;
  filterCounts: {
    all: number;
    media: number;
    text: number;
    video: number;
  };
}
