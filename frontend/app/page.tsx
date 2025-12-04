import { redirect } from 'next/navigation';

/**
 * 根页面 - 重定向到 Dashboard
 *
 * 根路由 (/) 自动跳转到 /dashboard，
 * 所有业务功能都在 /dashboard 路由下。
 */
export default function HomePage() {
  redirect('/dashboard');
}
