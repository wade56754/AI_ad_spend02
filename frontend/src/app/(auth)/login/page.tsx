/**
 * Login Page
 *
 * Route: /login
 * SoT 对齐: AUTH_SPEC.md v2.0
 */

import { LoginPage } from '@/features/auth';

export const metadata = {
  title: '登录 | AI 广告投放系统',
  description: '登录到 AI 广告投放管理系统',
};

export default function LoginRoute() {
  return <LoginPage />;
}
