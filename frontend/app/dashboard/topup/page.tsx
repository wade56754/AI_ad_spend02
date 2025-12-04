import PageContainer from '@/components/layout/page-container';
import { DollarSign } from 'lucide-react';

export const metadata = {
  title: '充值管理 - AI广告代投系统',
};

export default function TopupPage() {
  return (
    <PageContainer>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <DollarSign className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">充值管理</h1>
            <p className="text-sm text-muted-foreground">
              管理账户充值请求，审批流程和充值记录
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            充值列表占位 — 后续接入充值申请、审批和账本联动功能
          </p>
        </div>
      </div>
    </PageContainer>
  );
}
