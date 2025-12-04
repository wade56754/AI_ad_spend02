import PageContainer from '@/components/layout/page-container';
import { BookOpen } from 'lucide-react';

export const metadata = {
  title: '账本查询 - AI广告代投系统',
};

export default function LedgerPage() {
  return (
    <PageContainer>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <BookOpen className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">账本查询</h1>
            <p className="text-sm text-muted-foreground">
              查询账本流水，包括充值、消费、调整等所有账目记录
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            账本流水占位 — 后续接入双账本查询、余额计算和流水筛选功能
          </p>
        </div>
      </div>
    </PageContainer>
  );
}
