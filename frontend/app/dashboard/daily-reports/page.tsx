import PageContainer from '@/components/layout/page-container';
import { FileText } from 'lucide-react';

export const metadata = {
  title: '日报管理 - AI广告代投系统',
};

export default function DailyReportsPage() {
  return (
    <PageContainer>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">日报管理</h1>
            <p className="text-sm text-muted-foreground">
              管理投放日报，支持 8 状态流转（raw_submitted → final_locked）
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            日报列表占位 — 后续接入 DataTable、状态流转和趋势检查功能
          </p>
        </div>
      </div>
    </PageContainer>
  );
}
