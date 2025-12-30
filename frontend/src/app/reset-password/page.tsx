import type { Metadata } from 'next';
import { Suspense } from 'react';
import { ResetPasswordPage } from '@/features/auth/components/ResetPasswordPage';

export const metadata: Metadata = {
  title: '重置密码 | AI 广告代投系统',
  description: '设置新密码',
};

function ResetPasswordLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">加载中...</p>
      </div>
    </div>
  );
}

export default function ResetPassword() {
  return (
    <Suspense fallback={<ResetPasswordLoading />}>
      <ResetPasswordPage />
    </Suspense>
  );
}


