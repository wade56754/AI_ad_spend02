import PageContainer from '@/components/layout/page-container';
import { LayoutDashboard } from 'lucide-react';

export const metadata = {
  title: '项目管理 - AI广告代投系统',
};

export default function ProjectsPage() {
  return (
    <PageContainer>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <LayoutDashboard className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">项目管理</h1>
            <p className="text-sm text-muted-foreground">
              管理广告投放项目，查看项目状态和数据
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            项目列表占位 — 后续接入 DataTable 和项目 CRUD 功能
          </p>
        </div>
      </div>
    </PageContainer>
  );
}
