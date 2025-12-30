import type { Metadata } from 'next';
import { ForgotPasswordPage } from '@/features/auth/components/ForgotPasswordPage';

export const metadata: Metadata = {
  title: '忘记密码 | AI 广告代投系统',
  description: '重置您的密码',
};

export default function ForgotPassword() {
  return <ForgotPasswordPage />;
}


