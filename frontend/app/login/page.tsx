import { redirect } from 'next/navigation';

/**
 * /login 路由别名页面
 * 
 * 将 /login 重定向到 /auth/login，保留查询参数
 * 这样既保持了 /login 的简洁路由，又不需要移动现有文件结构
 */
export default function LoginAliasPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined };
}) {
  // 构建重定向 URL，保留所有查询参数
  const params = new URLSearchParams();
  Object.entries(searchParams).forEach(([key, value]) => {
    if (value) {
      if (Array.isArray(value)) {
        value.forEach(v => params.append(key, v));
      } else {
        params.append(key, value);
      }
    }
  });

  const queryString = params.toString();
  const redirectUrl = queryString ? `/auth/login?${queryString}` : '/auth/login';

  redirect(redirectUrl);
}

