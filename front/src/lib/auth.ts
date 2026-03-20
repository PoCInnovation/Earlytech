import { cookies } from "next/headers";

export async function getSession(): Promise<{ userId: string } | null> {
  const cookieStore = await cookies();
  const userId = cookieStore.get("userId")?.value;
  if (!userId) return null;
  return { userId };
}

export async function setAuthCookies(token: string, userId: string) {
  const cookieStore = await cookies();
  const maxAge = 60 * 60 * 24 * 7; // 7 days

  cookieStore.set("authToken", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge,
    path: "/",
  });

  cookieStore.set("userId", userId, {
    httpOnly: false,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge,
    path: "/",
  });
}

export async function deleteAuthCookies() {
  const cookieStore = await cookies();
  cookieStore.delete("authToken");
  cookieStore.delete("userId");
}

export function decodeJWT(token: string): { sub: string; role: string; exp: number; iat: number } {
  const payload = token.split(".")[1];
  const decoded = Buffer.from(payload, "base64url").toString("utf-8");
  return JSON.parse(decoded);
}
