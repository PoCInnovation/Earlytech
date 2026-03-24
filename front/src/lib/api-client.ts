import type {
  ArticleListResponse,
  Article,
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  UserKeyword,
  FeedResponse,
  UserStats,
  UserPreferences,
  UpdateUserPreferencesRequest,
  UserExclusionResponse,
  UserExcludedKeyword,
  UserFeedbackRequest,
  UserQualityStats,
} from "@/types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function getBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.API_URL || "http://localhost:3000";
  }
  return "/api";
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${getBaseUrl()}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.error || response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  register: (data: RegisterRequest) =>
    request<RegisterResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginRequest) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getArticles: () => request<ArticleListResponse>("/articles"),

  getArticle: (id: string) =>
    request<Article>(`/articles/${encodeURIComponent(id)}`),

  getArticleCount: () => request<{ count: number }>("/articles/count"),

  getUserKeywords: (userId: string) =>
    request<UserKeyword[]>(`/users/${userId}/keywords`),

  addKeyword: (userId: string, keyword: string) =>
    request<UserKeyword>(`/users/${userId}/keywords`, {
      method: "POST",
      body: JSON.stringify({ keyword }),
    }),

  deleteKeyword: (userId: string, keywordId: string) =>
    request<void>(`/users/${userId}/keywords/${keywordId}`, {
      method: "DELETE",
    }),

  getUserFeed: (userId: string) =>
    request<FeedResponse>(`/users/${userId}/feed`),

  getUserStats: (userId: string) =>
    request<UserStats>(`/users/${userId}/stats`),

  getUserPreferences: (userId: string) =>
    request<UserPreferences>(`/users/${userId}/preferences`),

  updateUserPreferences: (userId: string, data: UpdateUserPreferencesRequest) =>
    request<UserPreferences>(`/users/${userId}/preferences`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getUserExclusions: (userId: string) =>
    request<UserExclusionResponse>(`/users/${userId}/exclusions`),

  addExcludedSource: (userId: string, source: string) =>
    request<void>(`/users/${userId}/exclusions/sources`, {
      method: "POST",
      body: JSON.stringify({ source }),
    }),

  deleteExcludedSource: (userId: string, source: string) =>
    request<void>(`/users/${userId}/exclusions/sources/${encodeURIComponent(source)}`, {
      method: "DELETE",
    }),

  addExcludedKeyword: (userId: string, keyword: string) =>
    request<UserExcludedKeyword>(`/users/${userId}/exclusions/keywords`, {
      method: "POST",
      body: JSON.stringify({ keyword }),
    }),

  deleteExcludedKeyword: (userId: string, keywordId: string) =>
    request<void>(`/users/${userId}/exclusions/keywords/${keywordId}`, {
      method: "DELETE",
    }),

  submitFeedback: (userId: string, data: UserFeedbackRequest) =>
    request<void>(`/users/${userId}/feedback`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getUserQualityStats: (userId: string) =>
    request<UserQualityStats>(`/users/${userId}/quality`),
};
