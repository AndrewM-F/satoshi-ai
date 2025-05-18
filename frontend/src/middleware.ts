import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs';

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  const supabase = createMiddlewareClient({ req, res });

  // Refresh the session if it exists
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Auth logic based on route
  const path = req.nextUrl.pathname;

  // Protected routes - redirect to login if no session
  if (path.startsWith('/dashboard')) {
    if (!session) {
      const redirectUrl = new URL('/login', req.url);
      redirectUrl.searchParams.set('redirectedFrom', path);
      return NextResponse.redirect(redirectUrl);
    }
  }

  // Auth routes - redirect to dashboard if already logged in
  if ((path === '/login' || path === '/signup') && session) {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }

  return res;
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*', '/login', '/signup'],
};
