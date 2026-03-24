"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { api, ApiError } from "@/lib/api-client";

function getUserIdFromCookie(cookieStore: Awaited<ReturnType<typeof cookies>>): string | null {
  return cookieStore.get("userId")?.value ?? null;
}

export async function saveDigestPreferences(
  _prevState: { error?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string }> {
  const cookieStore = await cookies();
  const userId = getUserIdFromCookie(cookieStore);
  if (!userId) return { error: "Not authenticated" };

  const digestEnabled = formData.get("digest_enabled") === "on";
  const digestFrequency = (formData.get("digest_frequency") as string) === "weekly" ? "weekly" : "daily";
  const digestHourUtc = Number(formData.get("digest_hour_utc") ?? "8");

  if (!Number.isInteger(digestHourUtc) || digestHourUtc < 0 || digestHourUtc > 23) {
    return { error: "Digest hour must be between 0 and 23" };
  }

  try {
    await api.updateUserPreferences(userId, {
      digest_enabled: digestEnabled,
      digest_frequency: digestFrequency,
      digest_hour_utc: digestHourUtc,
    });
  } catch {
    return { error: "Failed to save preferences" };
  }

  revalidatePath("/settings");
  return {};
}

export async function addExcludedSource(source: string): Promise<{ error?: string }> {
  const cookieStore = await cookies();
  const userId = getUserIdFromCookie(cookieStore);
  if (!userId) return { error: "Not authenticated" };

  try {
    await api.addExcludedSource(userId, source);
  } catch (err) {
    if (err instanceof ApiError && err.status === 400) {
      return { error: err.message };
    }
    return { error: "Failed to exclude source" };
  }

  revalidatePath("/settings");
  revalidatePath("/feed");
  return {};
}

export async function deleteExcludedSource(source: string): Promise<{ error?: string }> {
  const cookieStore = await cookies();
  const userId = getUserIdFromCookie(cookieStore);
  if (!userId) return { error: "Not authenticated" };

  try {
    await api.deleteExcludedSource(userId, source);
  } catch {
    return { error: "Failed to remove excluded source" };
  }

  revalidatePath("/settings");
  revalidatePath("/feed");
  return {};
}

export async function addExcludedKeyword(
  _prevState: { error?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string }> {
  const cookieStore = await cookies();
  const userId = getUserIdFromCookie(cookieStore);
  if (!userId) return { error: "Not authenticated" };

  const keyword = (formData.get("keyword") as string | null)?.trim();
  if (!keyword) return { error: "Keyword is required" };

  try {
    await api.addExcludedKeyword(userId, keyword);
  } catch (err) {
    if (err instanceof ApiError && err.status === 400) {
      return { error: err.message };
    }
    return { error: "Failed to add excluded keyword" };
  }

  revalidatePath("/settings");
  revalidatePath("/feed");
  return {};
}

export async function deleteExcludedKeyword(keywordId: string): Promise<{ error?: string }> {
  const cookieStore = await cookies();
  const userId = getUserIdFromCookie(cookieStore);
  if (!userId) return { error: "Not authenticated" };

  try {
    await api.deleteExcludedKeyword(userId, keywordId);
  } catch {
    return { error: "Failed to remove excluded keyword" };
  }

  revalidatePath("/settings");
  revalidatePath("/feed");
  return {};
}