"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { api } from "@/lib/api-client";

export async function submitArticleFeedback(
  articleId: string,
  feedback: "relevant" | "not_relevant",
): Promise<{ error?: string }> {
  const cookieStore = await cookies();
  const userId = cookieStore.get("userId")?.value;

  if (!userId) return { error: "Not authenticated" };

  try {
    await api.submitFeedback(userId, {
      article_id: articleId,
      feedback,
    });
  } catch {
    return { error: "Failed to save feedback" };
  }

  revalidatePath("/feed");
  return {};
}