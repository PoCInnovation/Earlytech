"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { api, ApiError } from "@/lib/api-client";

export async function addKeyword(
  _prevState: { error?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string }> {
  const cookieStore = await cookies();
  const userId = cookieStore.get("userId")?.value;
  if (!userId) return { error: "Not authenticated" };

  const keyword = (formData.get("keyword") as string)?.trim();
  if (!keyword || keyword.length > 100) {
    return { error: "Keyword must be between 1 and 100 characters" };
  }

  try {
    await api.addKeyword(userId, keyword);
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      return { error: "This keyword already exists" };
    }
    return { error: "Failed to add keyword" };
  }

  revalidatePath("/settings");
  return {};
}

export async function deleteKeyword(keywordId: string): Promise<{ error?: string }> {
  const cookieStore = await cookies();
  const userId = cookieStore.get("userId")?.value;
  if (!userId) return { error: "Not authenticated" };

  try {
    await api.deleteKeyword(userId, keywordId);
  } catch {
    return { error: "Failed to delete keyword" };
  }

  revalidatePath("/settings");
  return {};
}
