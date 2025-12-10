/**
 * Topups Page Component
 *
 * Main page for topup request management with filters and statistics
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

'use client';

import { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Plus,
  Filter,
  RefreshCw,
  Download,
  ClipboardCheck,
  Wallet,
  CheckCircle,
  Ban,
  TrendingUp,
  DollarSign,
  FileText,
} from 'lucide-react';
import { useTopups, useTopupStats } from '../hooks';
import { TopupsTable } from './TopupsTable';
import { TopupRequestForm } from './TopupRequestForm';
import {
  TopupStatusBadge,
  TopupStatsCard,
  TopupStatusLegend,
  TopupAmount,
} from './TopupStatusBadge';
import {
  TopupApprovalDialog,
  TopupSubmitDialog,
  TopupCancelDialog,
} from './TopupApprovalDialog';
import { TopupApprovalTimeline } from './TopupApprovalTimeline';
import type { TopupRequest, TopupStatus, TopupListParams } from '../types';

// === Types ===

type TabValue = 'all' | 'pending_review' | 'finance_approve' | 'paid' | 'completed' | 'rejected';

interface FilterState {
  status: TopupStatus | '';
  project_id: string;
  start_date: string;
  end_date: string;
  min_amount: string;
  max_amount: string;
}

// === Stats Overview Component ===

interface StatsOverviewProps {
  stats: { by_status: Record<TopupStatus, number>; total_amount: number; pending_count: number } | undefined;
  isLoading: boolean;
  onFilterByStatus: (status: TopupStatus) => void;
}

function StatsOverview({ stats, isLoading, onFilterByStatus }: StatsOverviewProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4">
              <div className="h-4 w-16 bg-muted rounded mb-2" />
              <div className="h-8 w-24 bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const pendingReviewCount = stats?.by_status?.pending_review ?? 0;
  const financeApproveCount = stats?.by_status?.finance_approve ?? 0;
  const totalCount = stats ? Object.values(stats.by_status || {}).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <TopupStatsCard
        title="待数据复核"
        value={pendingReviewCount}
        icon={ClipboardCheck}
        variant="warning"
        onClick={() => onFilterByStatus('pending_review')}
      />
      <TopupStatsCard
        title="待财务终审"
        value={financeApproveCount}
        icon={Wallet}
        variant="info"
        onClick={() => onFilterByStatus('finance_approve')}
      />
      <TopupStatsCard
        title="待处理"
        value={stats?.pending_count ?? 0}
        icon={TrendingUp}
        variant="warning"
      />
      <TopupStatsCard
        title="总充值额"
        value={stats ? `¥${((stats.total_amount || 0) / 100).toLocaleString()}` : '¥0'}
        icon={DollarSign}
        variant="success"
      />
      <TopupStatsCard
        title="总申请数"
        value={totalCount}
        icon={CheckCircle}
        variant="default"
      />
      <TopupStatsCard
        title="已完成"
        value={stats?.by_status?.completed ?? 0}
        icon={FileText}
        variant="success"
      />
    </div>
  );
}

// === Filter Panel Component ===

interface FilterPanelProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onReset: () => void;
}

function FilterPanel({ filters, onFiltersChange, onReset }: FilterPanelProps) {
  const statusOptions: { value: TopupStatus | ''; label: string }[] = [
    { value: '', label: '全部状态' },
    { value: 'draft', label: '草稿' },
    { value: 'pending_review', label: '待数据复核' },
    { value: 'finance_approve', label: '待财务终审' },
    { value: 'paid', label: '已支付' },
    { value: 'completed', label: '已完成' },
    { value: 'rejected', label: '已拒绝' },
    { value: 'cancelled', label: '已取消' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <div className="space-y-2">
        <Label>状态筛选</Label>
        <Select
          value={filters.status}
          onValueChange={(value) =>
            onFiltersChange({ ...filters, status: value as TopupStatus | '' })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>开始日期</Label>
        <Input
          type="date"
          value={filters.start_date}
          onChange={(e) => onFiltersChange({ ...filters, start_date: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>结束日期</Label>
        <Input
          type="date"
          value={filters.end_date}
          onChange={(e) => onFiltersChange({ ...filters, end_date: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>最小金额(元)</Label>
        <Input
          type="number"
          placeholder="0"
          value={filters.min_amount}
          onChange={(e) => onFiltersChange({ ...filters, min_amount: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>最大金额(元)</Label>
        <Input
          type="number"
          placeholder="不限"
          value={filters.max_amount}
          onChange={(e) => onFiltersChange({ ...filters, max_amount: e.target.value })}
        />
      </div>

      <div className="flex items-end">
        <Button variant="outline" onClick={onReset} className="w-full">
          重置筛选
        </Button>
      </div>
    </div>
  );
}

// === Topup Detail Dialog ===

interface TopupDetailDialogProps {
  topup: TopupRequest | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAction: (action: 'data_review' | 'finance_approval' | 'complete' | 'cancel' | 'submit') => void;
  userRole: string;
}

function TopupDetailDialog({
  topup,
  open,
  onOpenChange,
  onAction,
  userRole,
}: TopupDetailDialogProps) {
  if (!topup) return null;

  const canDataReview =
    topup.status === 'pending_review' &&
    ['data_operator', 'admin'].includes(userRole);
  const canFinanceApprove =
    topup.status === 'finance_approve' &&
    ['finance', 'admin'].includes(userRole);
  const canComplete =
    topup.status === 'paid' &&
    ['finance', 'system', 'admin'].includes(userRole);
  const canCancel =
    ['draft', 'pending_review', 'finance_approve'].includes(topup.status) &&
    ['media_buyer', 'account_manager', 'admin'].includes(userRole);
  const canSubmit =
    topup.status === 'draft' &&
    ['media_buyer', 'account_manager', 'admin'].includes(userRole);

  // Handle Money type - could be number or object
  const amountValue = typeof topup.amount === 'number'
    ? topup.amount
    : (topup.amount as { value?: number })?.value ?? 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[540px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            充值申请详情
          </DialogTitle>
          <DialogDescription>
            查看充值申请的详细信息和审批历史
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Status Badge */}
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">当前状态</span>
            <TopupStatusBadge status={topup.status} size="lg" />
          </div>

          {/* Amount */}
          <div className="flex items-center justify-between py-4 border-y">
            <span className="text-muted-foreground">充值金额</span>
            <TopupAmount amount={amountValue} currency={topup.currency} size="lg" />
          </div>

          {/* Basic Info */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground">基本信息</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-muted-foreground">项目</span>
                <p className="font-medium">{topup.project_name || topup.project_id.slice(0, 8)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">广告账户</span>
                <p className="font-medium">{topup.ad_account_name || '-'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">申请人</span>
                <p className="font-medium">{topup.requested_by_name || '-'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">申请时间</span>
                <p className="font-medium">
                  {new Date(topup.requested_at).toLocaleString('zh-CN')}
                </p>
              </div>
            </div>
            {topup.notes && (
              <div>
                <span className="text-muted-foreground text-sm">备注</span>
                <p className="text-sm mt-1 p-2 bg-muted rounded">{topup.notes}</p>
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground">审批历史</h4>
            <TopupApprovalTimeline topup={topup} showDetails />
          </div>

          {/* Actions */}
          <div className="space-y-2 pt-4 border-t">
            {canSubmit && (
              <Button onClick={() => onAction('submit')} className="w-full">
                <CheckCircle className="h-4 w-4 mr-2" />
                提交审批
              </Button>
            )}
            {canDataReview && (
              <Button onClick={() => onAction('data_review')} className="w-full">
                <ClipboardCheck className="h-4 w-4 mr-2" />
                数据复核
              </Button>
            )}
            {canFinanceApprove && (
              <Button onClick={() => onAction('finance_approval')} className="w-full">
                <Wallet className="h-4 w-4 mr-2" />
                财务终审
              </Button>
            )}
            {canComplete && (
              <Button onClick={() => onAction('complete')} className="w-full">
                <CheckCircle className="h-4 w-4 mr-2" />
                确认到账
              </Button>
            )}
            {canCancel && (
              <Button variant="outline" onClick={() => onAction('cancel')} className="w-full">
                <Ban className="h-4 w-4 mr-2" />
                取消申请
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// === Main Page Component ===

export function TopupsPage() {
  // State
  const [activeTab, setActiveTab] = useState<TabValue>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    status: '',
    project_id: '',
    start_date: '',
    end_date: '',
    min_amount: '',
    max_amount: '',
  });

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

  // Data fetching
  const { refetch } = useTopups(queryParams);
  const { data: statsData, isLoading: isStatsLoading } = useTopupStats();

  // Handlers
  const handleResetFilters = useCallback(() => {
    setFilters({
      status: '',
      project_id: '',
      start_date: '',
      end_date: '',
      min_amount: '',
      max_amount: '',
    });
  }, []);

  const handleFilterByStatus = useCallback((status: TopupStatus) => {
    setActiveTab(status as TabValue);
  }, []);

  const handleViewDetail = useCallback((topup: TopupRequest) => {
    setSelectedTopup(topup);
    setShowDetail(true);
  }, []);

  const handleDetailAction = useCallback(
    (action: 'data_review' | 'finance_approval' | 'complete' | 'cancel' | 'submit') => {
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
    refetch();
    setSelectedTopup(null);
    setApprovalMode(null);
    setShowSubmitDialog(false);
    setShowCancelDialog(false);
  }, [refetch]);

  const handleCreateFormSubmit = useCallback(async (data: unknown) => {
    // Handle form submission
    console.log('Create topup:', data);
    setShowCreateForm(false);
    refetch();
  }, [refetch]);

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
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">充值管理</h1>
          <p className="text-muted-foreground">
            管理项目充值申请与双重审核流程
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
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

      {/* Stats Overview */}
      <StatsOverview
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
        <Card>
          <CardContent className="pt-6">
            <FilterPanel
              filters={filters}
              onFiltersChange={setFilters}
              onReset={handleResetFilters}
            />
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
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
  );
}

export default TopupsPage;
