"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { logout } from "@/actions/auth";

interface MobileMenuProps {
  isAuth: boolean;
}

export function MobileMenu({ isAuth }: MobileMenuProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="sm:hidden">
      <button
        onClick={() => setOpen(!open)}
        className="p-2 text-text-secondary hover:text-text-primary"
        aria-label="Toggle menu"
      >
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>

      {open && (
        <div className="absolute top-16 left-0 right-0 bg-surface border-b border-border z-50">
          <nav className="flex flex-col px-4 py-4 gap-3">
            {isAuth ? (
              <>
                <Link href="/" onClick={() => setOpen(false)} className="text-sm text-text-secondary py-2">
                  Home
                </Link>
                <Link href="/feed" onClick={() => setOpen(false)} className="text-sm text-text-secondary py-2">
                  My feed
                </Link>
                <Link href="/settings" onClick={() => setOpen(false)} className="text-sm text-text-secondary py-2">
                  Settings
                </Link>
                <form action={logout}>
                  <button type="submit" className="text-sm text-text-secondary py-2">
                    Log out
                  </button>
                </form>
              </>
            ) : (
              <>
                <Link href="/login" onClick={() => setOpen(false)} className="text-sm text-text-secondary py-2">
                  Log in
                </Link>
                <Link href="/register" onClick={() => setOpen(false)} className="text-sm text-text-secondary py-2">
                  Sign up
                </Link>
              </>
            )}
          </nav>
        </div>
      )}
    </div>
  );
}
