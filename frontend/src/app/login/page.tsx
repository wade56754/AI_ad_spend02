import type { Metadata } from 'next';
import { LoginPage } from '@/features/auth/components/LoginPage';

export const metadata: Metadata = {
  title: '登录 | AI 广告代投系统',
  description: '登录 AI 广告代投系统',
};

export default function Login() {
  return <LoginPage />;
}
