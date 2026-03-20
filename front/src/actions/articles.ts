"use server";

import { api } from "@/lib/api-client";
import type { ArticleListResponse, FeedResponse, UserStats } from "@/types";

export async function getArticles(): Promise<ArticleListResponse | null> {
  try {
    return await api.getArticles();
  } catch {
    return null;
  }
}

export async function getUserFeed(userId: string): Promise<FeedResponse | null> {
  try {
    return await api.getUserFeed(userId);
  } catch {
    return null;
  }
}

export async function getUserStats(userId: string): Promise<UserStats | null> {
  try {
    return await api.getUserStats(userId);
  } catch {
    return null;
  }
}
