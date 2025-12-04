import PageContainer from '@/components/layout/page-container';
import { Users } from 'lucide-react';

export const metadata = {
  title: '渠道账户 - AI广告代投系统',
};

export default function AdAccountsPage() {
  return (
    <PageContainer>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Users className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">渠道账户</h1>
            <p className="text-sm text-muted-foreground">
              管理广告渠道账户，包括账户余额、状态和关联项目
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            渠道账户列表占位 — 后续接入账户管理和余额查询功能
          </p>
        </div>
      </div>
    </PageContainer>
  );
}
