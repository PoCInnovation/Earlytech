import Link from "next/link";
import { cookies } from "next/headers";
import { logout } from "@/actions/auth";
import { MobileMenu } from "./mobile-menu";

export async function Header() {
  const cookieStore = await cookies();
  const isAuth = !!cookieStore.get("authToken")?.value;

  return (
    <header className="border-b border-border bg-surface">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link href="/" className="font-serif text-xl font-bold text-text-primary">
          EarlyTech
        </Link>

        <nav className="hidden sm:flex items-center gap-6">
          {isAuth ? (
            <>
              <Link href="/" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
                Home
              </Link>
              <Link href="/feed" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
                My feed
              </Link>
              <Link href="/settings" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
                Settings
              </Link>
              <form action={logout}>
                <button type="submit" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
                  Log out
                </button>
              </form>
            </>
          ) : (
            <>
              <Link href="/login" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
                Log in
              </Link>
              <Link
                href="/register"
                className="text-sm px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors"
              >
                Sign up
              </Link>
            </>
          )}
        </nav>

        <MobileMenu isAuth={isAuth} />
      </div>
    </header>
  );
}
