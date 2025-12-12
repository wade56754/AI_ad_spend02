import type { Metadata } from 'next';
import { RegisterPage } from '@/features/auth/components/RegisterPage';

export const metadata: Metadata = {
  title: '注册 | AI 广告代投系统',
  description: '注册 AI 广告代投系统账户',
};

export default function Register() {
  return <RegisterPage />;
}
