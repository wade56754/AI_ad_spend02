/**
 * TopupsPage Component
 *
 * SoT: docs/10.module-specs/B1-topup-approval.md §3.1 页面布局
 * SoT: STATE_MACHINE.md v2.6 Section 3 (充值 7 状态机)
 * SoT: API_SOT.md v9.0 Section 5.6 (Topup endpoints)
 *
 * 一句话定义: 让财务/项目负责人了解"有哪些充值申请？谁在等审批？"
 *
 * 充值 7 状态机:
 *   draft → pending_review → finance_approve → paid → completed
 *                  ↓              ↓
 *              rejected       rejected
 *
 * @module features/topups/components
 */

'use client';

import { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Filter, RefreshCw, Download } from 'lucide-react';
import { useTopups, useTopupStats, useRefreshTopups } from '../hooks';
import { TopupsTable } from './TopupsTable';
import { TopupRequestForm } from './TopupRequestForm';
import { TopupStatusLegend } from './TopupStatusBadge';
import {
  TopupApprovalDialog,
  TopupSubmitDialog,
  TopupCancelDialog,
} from './TopupApprovalDialog';
import { TopupsStatsOverview } from './TopupsStatsOverview';
import { TopupsFilterPanel, type FilterState, initialFilterState } from './TopupsFilterPanel';
import { TopupDetailDialog, type TopupDialogAction } from './TopupDetailDialog';
import type { TopupRequest, TopupStatus, TopupListParams } from '../types';

// === Types ===

type TabValue = 'all' | 'pending_review' | 'finance_approve' | 'paid' | 'completed' | 'rejected';

// === Main Page Component ===

export function TopupsPage() {
  // State
  const [activeTab, setActiveTab] = useState<TabValue>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filters, setFilters] = useState<FilterState>(initialFilterState);

  // Selected topup for actions
  const [selectedTopup, setSelectedTopup] = useState<TopupRequest | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [approvalMode, setApprovalMode] = useState<
    'data_review' | 'finance_approval' | 'complete' | 'cancel' | null
  >(null);
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);

  // User role (would come from auth context in real app)
  const userRole = 'admin'; // TODO: Get from useAuth()

  // Build query params
  const queryParams = useMemo<TopupListParams>(() => {
    const params: TopupListParams = {
      page: 1,
      page_size: 20,
    };

    // Tab filter
    if (activeTab !== 'all') {
      params.status = activeTab as TopupStatus;
    } else if (filters.status) {
      params.status = filters.status;
    }

    if (filters.start_date) params.start_date = filters.start_date;
    if (filters.end_date) params.end_date = filters.end_date;
    if (filters.min_amount)
      params.min_amount = Math.round(parseFloat(filters.min_amount) * 100);
    if (filters.max_amount)
      params.max_amount = Math.round(parseFloat(filters.max_amount) * 100);

    return params;
  }, [activeTab, filters]);

  // Data fetching - SoT: B1-topup-approval.md §5 API 接口
  useTopups(queryParams);
  const { data: statsData, isLoading: isStatsLoading } = useTopupStats();

  // 刷新 hook - SoT: B1-topup-approval.md §2.4 数据刷新策略
  const { refreshAll } = useRefreshTopups();

  // Handlers
  const handleResetFilters = useCallback(() => {
    setFilters(initialFilterState);
  }, []);

  const handleFilterByStatus = useCallback((status: TopupStatus) => {
    setActiveTab(status as TabValue);
  }, []);

  const handleViewDetail = useCallback((topup: TopupRequest) => {
    setSelectedTopup(topup);
    setShowDetail(true);
  }, []);

  const handleDetailAction = useCallback(
    (action: TopupDialogAction) => {
      setShowDetail(false);
      if (action === 'submit') {
        setShowSubmitDialog(true);
      } else if (action === 'cancel') {
        setShowCancelDialog(true);
      } else {
        setApprovalMode(action);
      }
    },
    []
  );

  const handleActionSuccess = useCallback(() => {
    refreshAll();
    setSelectedTopup(null);
    setApprovalMode(null);
    setShowSubmitDialog(false);
    setShowCancelDialog(false);
  }, [refreshAll]);

  const handleCreateFormSubmit = useCallback(async (_data: unknown) => {
    // TODO: Implement actual form submission via API
    setShowCreateForm(false);
    refreshAll();
  }, [refreshAll]);

  // Tab counts from stats
  const tabCounts = useMemo(() => {
    if (!statsData?.by_status) return {} as Record<string, number>;
    return statsData.by_status;
  }, [statsData]);

  const totalCount = useMemo(() => {
    if (!statsData?.by_status) return 0;
    return Object.values(statsData.by_status).reduce((a, b) => a + b, 0);
  }, [statsData]);

  return (
    <div className="min-h-screen bg-gray-50 -m-6 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
      {/* Header - v3.0 白色卡片头部 */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100">
              <Plus className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">充值管理</h1>
              <p className="text-sm text-gray-500">
                管理项目充值申请与双重审核流程
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => refreshAll()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              导出
            </Button>
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              新建申请
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <TopupsStatsOverview
        stats={statsData}
        isLoading={isStatsLoading}
        onFilterByStatus={handleFilterByStatus}
      />

      {/* Filters Toggle */}
      <div className="flex items-center justify-between">
        <Button
          variant={showFilters ? 'secondary' : 'outline'}
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="h-4 w-4 mr-2" />
          {showFilters ? '收起筛选' : '展开筛选'}
        </Button>
        <TopupStatusLegend />
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <TopupsFilterPanel
            filters={filters}
            onFiltersChange={setFilters}
            onReset={handleResetFilters}
          />
        </div>
      )}

      {/* Tabs - 白色卡片容器 */}
      <div className="bg-white rounded-xl shadow-sm p-6">
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)}>
        <TabsList>
          <TabsTrigger value="all">
            全部
            {totalCount > 0 ? ` (${totalCount})` : ''}
          </TabsTrigger>
          <TabsTrigger value="pending_review">
            待数据复核
            {tabCounts.pending_review ? ` (${tabCounts.pending_review})` : ''}
          </TabsTrigger>
          <TabsTrigger value="finance_approve">
            待财务终审
            {tabCounts.finance_approve ? ` (${tabCounts.finance_approve})` : ''}
          </TabsTrigger>
          <TabsTrigger value="paid">
            已支付
            {tabCounts.paid ? ` (${tabCounts.paid})` : ''}
          </TabsTrigger>
          <TabsTrigger value="completed">
            已完成
            {tabCounts.completed ? ` (${tabCounts.completed})` : ''}
          </TabsTrigger>
          <TabsTrigger value="rejected">
            已拒绝
            {tabCounts.rejected ? ` (${tabCounts.rejected})` : ''}
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          <TopupsTable onViewDetail={handleViewDetail} />
        </TabsContent>
      </Tabs>
      </div>

      {/* Detail Dialog */}
      <TopupDetailDialog
        topup={selectedTopup}
        open={showDetail}
        onOpenChange={setShowDetail}
        onAction={handleDetailAction}
        userRole={userRole}
      />

      {/* Approval Dialog */}
      {approvalMode && (
        <TopupApprovalDialog
          open={!!approvalMode}
          onOpenChange={(open) => !open && setApprovalMode(null)}
          topup={selectedTopup}
          mode={approvalMode}
          userRole={userRole}
          onSuccess={handleActionSuccess}
        />
      )}

      {/* Submit Dialog */}
      <TopupSubmitDialog
        open={showSubmitDialog}
        onOpenChange={setShowSubmitDialog}
        topup={selectedTopup}
        onSuccess={handleActionSuccess}
      />

      {/* Cancel Dialog */}
      <TopupCancelDialog
        open={showCancelDialog}
        onOpenChange={setShowCancelDialog}
        topup={selectedTopup}
        onSuccess={handleActionSuccess}
      />

      {/* Create Form Dialog */}
      <TopupRequestForm
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onSubmit={handleCreateFormSubmit}
      />
      </div>
    </div>
  );
}

export default TopupsPage;
