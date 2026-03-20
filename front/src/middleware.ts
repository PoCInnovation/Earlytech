import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedRoutes = ["/feed", "/settings"];
const authRoutes = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasToken = !!request.cookies.get("authToken")?.value;

  if (protectedRoutes.some((route) => pathname.startsWith(route)) && !hasToken) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (authRoutes.some((route) => pathname.startsWith(route)) && hasToken) {
    return NextResponse.redirect(new URL("/feed", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/feed/:path*", "/settings/:path*", "/login", "/register"],
};
