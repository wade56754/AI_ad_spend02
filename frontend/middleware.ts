// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * 公开路由 - 无需认证即可访问
 */
const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password'];

/**
 * 检查路径是否为公开路由
 */
function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some((route) => pathname.startsWith(route));
}

/**
 * 检查路径是否为静态资源或API
 */
function isStaticOrApi(pathname: string): boolean {
  return (
    pathname.startsWith('/api') ||
    pathname.startsWith('/_next') ||
    pathname.includes('.') // 包含扩展名的文件
  );
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 跳过静态资源和API路由
  if (isStaticOrApi(pathname)) {
    return NextResponse.next();
  }

  // 从 cookie 或 localStorage 获取 token
  // 注意：middleware 只能访问 cookies，不能访问 localStorage
  const token = request.cookies.get('access_token')?.value;

  // 公开路由处理
  if (isPublicRoute(pathname)) {
    // 已登录用户访问公开路由 → 重定向到首页仪表盘
    if (token) {
      const url = request.nextUrl.clone();
      url.pathname = '/';
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  // 受保护路由处理（除公开路由外的所有路由）
  // 未登录用户 → 重定向到登录页
  if (!token) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    // 保存原始路径用于登录后跳转
    if (pathname !== '/') {
      url.searchParams.set('callbackUrl', pathname);
    }
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

/**
 * 配置 Middleware 匹配路径
 */
export const config = {
  matcher: [
    /*
     * 匹配所有路径除了:
     * - api (API routes)
     * - _next/static (静态文件)
     * - _next/image (图片优化)
     * - favicon.ico (图标)
     * - public 文件夹
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
