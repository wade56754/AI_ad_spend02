/**
 * 页面组件标准模式 - AI 广告代投系统
 * Version: 1.0
 * SoT Reference: STATE_MACHINE.md v2.6
 *
 * 本文件展示页面组件的标准写法，供 AI 代码生成参考。
 *
 * 关键模式：
 * 1. 'use client' 指令（Next.js App Router）
 * 2. 状态管理 (useState, useMemo, useCallback)
 * 3. 数据获取 (React Query hooks)
 * 4. 组件拆分（提取子组件）
 * 5. SoT 注释引用
 */

'use client';

import { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Filter, RefreshCw, Download } from 'lucide-react';

// === 类型定义 ===

interface ExampleItem {
  id: number;
  name: string;
  status: ExampleStatus;
  amount: number;
  created_at: string;
}

type ExampleStatus = 'draft' | 'pending_review' | 'approved' | 'rejected';

interface FilterState {
  status: ExampleStatus | null;
  start_date: string;
  end_date: string;
}

interface ListParams {
  page: number;
  page_size: number;
  status?: ExampleStatus;
  start_date?: string;
  end_date?: string;
}

// === 初始状态 ===

const initialFilterState: FilterState = {
  status: null,
  start_date: '',
  end_date: '',
};

// === Hooks 导入（假设已有） ===

// import { useExamples, useExampleStats } from '../hooks';
// import { useAuth } from '@/features/auth/hooks/useAuth';

// === 子组件导入 ===

// import { ExampleTable } from './ExampleTable';
// import { ExampleForm } from './ExampleForm';
// import { ExampleFilterPanel } from './ExampleFilterPanel';
// import { ExampleStatsOverview } from './ExampleStatsOverview';

// === 主页面组件 ===

export function ExamplePage() {
  // === State 管理 ===

  // Tab 状态
  const [activeTab, setActiveTab] = useState<'all' | ExampleStatus>('all');

  // 筛选状态
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterState>(initialFilterState);

  // 表单弹窗状态
  const [showCreateForm, setShowCreateForm] = useState(false);

  // 选中项状态（用于详情/操作）
  const [selectedItem, setSelectedItem] = useState<ExampleItem | null>(null);

  // === 查询参数构建 ===

  const queryParams = useMemo<ListParams>(() => {
    const params: ListParams = {
      page: 1,
      page_size: 20,
    };

    // Tab 筛选优先
    if (activeTab !== 'all') {
      params.status = activeTab;
    } else if (filters.status) {
      params.status = filters.status;
    }

    // 日期筛选
    if (filters.start_date) params.start_date = filters.start_date;
    if (filters.end_date) params.end_date = filters.end_date;

    return params;
  }, [activeTab, filters]);

  // === 数据获取 ===

  // const { data, isLoading, refetch } = useExamples(queryParams);
  // const { data: stats, isLoading: isStatsLoading } = useExampleStats();

  // 模拟数据
  const refetch = useCallback(() => {
    console.log('Refetching...');
  }, []);

  // === 事件处理器 ===

  const handleResetFilters = useCallback(() => {
    setFilters(initialFilterState);
  }, []);

  const handleFilterChange = useCallback((newFilters: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  }, []);

  const handleViewDetail = useCallback((item: ExampleItem) => {
    setSelectedItem(item);
  }, []);

  const handleCreateSuccess = useCallback(() => {
    setShowCreateForm(false);
    refetch();
  }, [refetch]);

  const handleActionSuccess = useCallback(() => {
    setSelectedItem(null);
    refetch();
  }, [refetch]);

  // === Tab 计数（从统计数据） ===

  const tabCounts = useMemo(() => {
    // 从 stats 数据获取各状态数量
    return {
      all: 100,
      draft: 10,
      pending_review: 20,
      approved: 60,
      rejected: 10,
    };
  }, []);

  // === 渲染 ===

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">示例管理</h1>
          <p className="text-muted-foreground">
            管理示例数据的完整生命周期
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            筛选
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            新建
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      {/* <ExampleStatsOverview stats={stats} isLoading={isStatsLoading} /> */}

      {/* 筛选面板（可折叠） */}
      {showFilters && (
        <Card>
          <CardContent className="pt-6">
            {/* <ExampleFilterPanel
              filters={filters}
              onChange={handleFilterChange}
              onReset={handleResetFilters}
            /> */}
            <div className="text-sm text-muted-foreground">
              筛选面板组件占位
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab 切换 + 数据表格 */}
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as typeof activeTab)}
      >
        <TabsList>
          <TabsTrigger value="all">
            全部 ({tabCounts.all})
          </TabsTrigger>
          <TabsTrigger value="draft">
            草稿 ({tabCounts.draft})
          </TabsTrigger>
          <TabsTrigger value="pending_review">
            待审核 ({tabCounts.pending_review})
          </TabsTrigger>
          <TabsTrigger value="approved">
            已通过 ({tabCounts.approved})
          </TabsTrigger>
          <TabsTrigger value="rejected">
            已拒绝 ({tabCounts.rejected})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          <Card>
            <CardContent className="pt-6">
              {/* <ExampleTable
                data={data?.items ?? []}
                isLoading={isLoading}
                onViewDetail={handleViewDetail}
              /> */}
              <div className="text-sm text-muted-foreground">
                数据表格组件占位
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 新建表单弹窗 */}
      {/* {showCreateForm && (
        <ExampleForm
          open={showCreateForm}
          onClose={() => setShowCreateForm(false)}
          onSuccess={handleCreateSuccess}
        />
      )} */}
    </div>
  );
}

// === 子组件模式：统计卡片 ===

interface StatsOverviewProps {
  stats: {
    total: number;
    total_amount: number;
    by_status: Record<string, number>;
  } | null;
  isLoading: boolean;
}

function StatsOverview({ stats, isLoading }: StatsOverviewProps) {
  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">总数量</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats?.total ?? 0}</div>
        </CardContent>
      </Card>
      {/* 更多统计卡片... */}
    </div>
  );
}

// === 导出 ===

export default ExamplePage;
