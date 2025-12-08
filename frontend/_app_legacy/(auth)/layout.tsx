import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '登录 - AI广告代投系统',
  description: '登录到AI广告代投系统',
};

/**
 * 认证页面布局
 * 居中卡片式布局，无侧边栏
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="w-full max-w-md p-4">
        {children}
      </div>
    </div>
  );
}
