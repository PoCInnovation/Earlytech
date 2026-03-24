export interface Article {
  id: string;
  title: string | null;
  url: string;
  source: string;
  content: string | null;
  summary: string | null;
  authors: string[] | null;
  published_date: string | null;
  scraped_at: string;
}

export interface ArticleListResponse {
  total: number;
  page: number;
  per_page: number;
  articles: Article[];
}

export interface ArticleWithDelivery {
  id: string;
  title: string | null;
  url: string;
  source: string;
  summary: string | null;
  published_date: string | null;
  matched_keyword: string;
  similarity_score: number;
  delivered_at: string;
  feedback?: "relevant" | "not_relevant" | null;
}

export interface FeedResponse {
  user_id: string;
  total_articles: number;
  articles: ArticleWithDelivery[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  status: string;
  user: { id: string };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  status: string;
  token: string;
}

export interface UserKeyword {
  id: string;
  user_id: string;
  keyword: string;
  created_at: string;
}

export interface AddKeywordRequest {
  keyword: string;
}

export interface UserStats {
  user_id: string;
  total_articles: number;
  total_keywords: number;
  avg_similarity: number;
  last_delivery: string | null;
}

export interface UserPreferences {
  user_id: string;
  digest_enabled: boolean;
  digest_frequency: "daily" | "weekly";
  digest_hour_utc: number;
  updated_at: string;
}

export interface UpdateUserPreferencesRequest {
  digest_enabled: boolean;
  digest_frequency: "daily" | "weekly";
  digest_hour_utc: number;
}

export interface UserExcludedKeyword {
  id: string;
  user_id: string;
  keyword: string;
  created_at: string;
}

export interface UserExclusionResponse {
  sources: string[];
  keywords: UserExcludedKeyword[];
}

export interface UserFeedbackRequest {
  article_id: string;
  feedback: "relevant" | "not_relevant";
}

export interface UserQualityStats {
  user_id: string;
  total_delivered: number;
  total_feedback: number;
  relevant_count: number;
  not_relevant_count: number;
  relevance_rate: number;
  feedback_coverage_rate: number;
  avg_similarity: number;
}

export type SourceType = "arxiv" | "github" | "medium" | "le_monde" | "huggingface";

export interface SourceConfig {
  label: string;
  color: string;
  icon: string;
}
