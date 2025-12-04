import PageContainer from '@/components/layout/page-container';
import { CheckSquare } from 'lucide-react';

export const metadata = {
  title: '对账管理 - AI广告代投系统',
};

export default function ReconciliationPage() {
  return (
    <PageContainer>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <CheckSquare className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">对账管理</h1>
            <p className="text-sm text-muted-foreground">
              管理账户对账批次，处理差异调整和对账确认
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            对账列表占位 — 后续接入对账批次、差异分析和调整功能
          </p>
        </div>
      </div>
    </PageContainer>
  );
}
