"use server";

import { z } from "zod/v4";
import { redirect } from "next/navigation";
import { api, ApiError } from "@/lib/api-client";
import { setAuthCookies, deleteAuthCookies, decodeJWT } from "@/lib/auth";

const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(50),
  email: z.email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

const loginSchema = z.object({
  email: z.email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

export async function register(
  _prevState: { error?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string }> {
  const raw = {
    name: formData.get("name") as string,
    email: formData.get("email") as string,
    password: formData.get("password") as string,
  };

  const parsed = registerSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }

  try {
    await api.register(parsed.data);
    const loginRes = await api.login({ email: parsed.data.email, password: parsed.data.password });
    const payload = decodeJWT(loginRes.token);
    await setAuthCookies(loginRes.token, payload.sub);
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      return { error: "This email is already in use" };
    }
    return { error: "Something went wrong. Please try again." };
  }

  redirect("/settings");
}

export async function login(
  _prevState: { error?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string }> {
  const raw = {
    email: formData.get("email") as string,
    password: formData.get("password") as string,
  };

  const parsed = loginSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }

  try {
    const res = await api.login(parsed.data);
    const payload = decodeJWT(res.token);
    await setAuthCookies(res.token, payload.sub);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      return { error: "Invalid email or password" };
    }
    return { error: "Something went wrong. Please try again." };
  }

  redirect("/feed");
}

export async function logout() {
  await deleteAuthCookies();
  redirect("/");
}
