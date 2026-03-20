"use client";

import { useActionState } from "react";
import Link from "next/link";
import { login } from "@/actions/auth";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function LoginForm() {
  const [state, formAction, pending] = useActionState(login, undefined);

  return (
    <form action={formAction} className="space-y-4">
      <Input name="email" type="email" placeholder="Email" required />
      <Input name="password" type="password" placeholder="Password" required />

      {state?.error && (
        <p className="text-sm text-error">{state.error}</p>
      )}

      <Button type="submit" disabled={pending} className="w-full">
        {pending ? "Logging in..." : "Log in"}
      </Button>

      <p className="text-sm text-center text-text-secondary">
        No account?{" "}
        <Link href="/register" className="text-text-primary font-medium hover:underline">
          Sign up
        </Link>
      </p>
    </form>
  );
}
