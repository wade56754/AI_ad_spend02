import PageContainer from '@/components/layout/page-container';
import { Settings } from 'lucide-react';

export const metadata = {
  title: '系统设置 - AI广告代投系统',
};

export default function SettingsPage() {
  return (
    <PageContainer>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Settings className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">系统设置</h1>
            <p className="text-sm text-muted-foreground">
              管理系统配置，包括用户权限、通知设置等
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            系统设置占位 — 后续接入用户管理、权限配置和系统参数功能
          </p>
        </div>
      </div>
    </PageContainer>
  );
}
