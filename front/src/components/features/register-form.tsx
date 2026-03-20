"use client";

import { useActionState } from "react";
import Link from "next/link";
import { register } from "@/actions/auth";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function RegisterForm() {
  const [state, formAction, pending] = useActionState(register, undefined);

  return (
    <form action={formAction} className="space-y-4">
      <Input name="name" type="text" placeholder="Name" required minLength={2} maxLength={50} />
      <Input name="email" type="email" placeholder="Email" required />
      <Input name="password" type="password" placeholder="Password" required minLength={6} />

      {state?.error && (
        <p className="text-sm text-error">{state.error}</p>
      )}

      <Button type="submit" disabled={pending} className="w-full">
        {pending ? "Signing up..." : "Sign up"}
      </Button>

      <p className="text-sm text-center text-text-secondary">
        Already have an account?{" "}
        <Link href="/login" className="text-text-primary font-medium hover:underline">
          Log in
        </Link>
      </p>
    </form>
  );
}
