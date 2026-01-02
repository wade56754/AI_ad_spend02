/**
 * PitcherWorkbench Component - 投手工作台
 *
 * SoT References:
 * - STATE_MACHINE.md v2.8 §7.5: Phase 1 日报 3 状态 (raw_submitted, trend_ok, final_confirmed)
 * - BR-RPT-001: 投手仅提交自己负责的账户日报
 * - BR-RPT-006: 仅 pitcher 提交 conversions_raw
 * - API_SOT.md v9.0: Daily Reports endpoints
 *
 * 一句话定义: 让投手快速填报日报、查看自己的数据和 KPI
 *
 * Phase 1 约束:
 * - 只显示 3 个状态: raw_submitted, trend_ok, final_confirmed
 * - 仅提示，不阻断
 *
 * @module features/daily-reports/components
 */

'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Plus,
  FileText,
  Clock,
  CheckCircle2,
  TrendingUp,
  DollarSign,
  Users,
  Target,
  RefreshCw,
  MoreHorizontal,
  Edit,
  Trash2,
  Eye,
  Calendar,
  AlertCircle,
} from 'lucide-react';
import { format, isToday, parseISO } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import {
  useDailyReports,
  useDailyReportStats,
  useDeleteDailyReport,
  useRefreshDailyReports,
} from '../hooks';
import { DailyReportForm } from './DailyReportForm';
import type { DailyReport, DailyReportStatus } from '../types';
import { apiFetch } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';

// ============================================================================
// 类型定义
// ============================================================================

interface AdAccount {
  id: number;
  name: string;
  platform: string;
  project_name?: string;
}

// Phase 1 状态配置 (只使用 3 个状态)
const PHASE1_STATUS_CONFIG: Record<
  string,
  { label: string; color: string; icon: typeof FileText }
> = {
  raw_submitted: { label: '已提交', color: 'bg-blue-100 text-blue-700', icon: FileText },
  trend_ok: { label: '趋势正常', color: 'bg-green-100 text-green-700', icon: TrendingUp },
  final_confirmed: {
    label: '已确认',
    color: 'bg-emerald-100 text-emerald-700',
    icon: CheckCircle2,
  },
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * 获取投手分配的广告账户
 */
function useMyAdAccounts() {
  return useQuery({
    queryKey: ['ad-accounts', 'my-accounts'],
    queryFn: async () => {
      // 获取当前用户分配的账户
      return apiFetch<AdAccount[]>('/api/v1/ad-accounts?assigned_to_me=true');
    },
    staleTime: 5 * 60 * 1000, // 5 分钟
  });
}

// ============================================================================
// 子组件 - KPI 卡片
// ============================================================================

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: { value: number; isPositive: boolean };
  color: 'blue' | 'green' | 'amber' | 'purple';
}

const colorConfig = {
  blue: { iconBg: 'bg-blue-50', iconColor: 'text-blue-600', ring: 'ring-blue-200' },
  green: { iconBg: 'bg-green-50', iconColor: 'text-green-600', ring: 'ring-green-200' },
  amber: { iconBg: 'bg-amber-50', iconColor: 'text-amber-600', ring: 'ring-amber-200' },
  purple: { iconBg: 'bg-purple-50', iconColor: 'text-purple-600', ring: 'ring-purple-200' },
};

function StatCard({ title, value, subtitle, icon: Icon, trend, color }: StatCardProps) {
  const colors = colorConfig[color];

  return (
    <Card className="bg-white shadow-sm hover:shadow-md transition-shadow">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-gray-500">{title}</p>
            <p className="text-2xl font-bold text-gray-900 tabular-nums">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
            {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
            {trend && (
              <p
                className={cn(
                  'text-xs font-medium',
                  trend.isPositive ? 'text-green-600' : 'text-red-600'
                )}
              >
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}% 较昨日
              </p>
            )}
          </div>
          <div
            className={cn('w-10 h-10 rounded-lg flex items-center justify-center', colors.iconBg)}
          >
            <Icon className={cn('h-5 w-5', colors.iconColor)} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// 子组件 - 状态标签
// ============================================================================

function StatusBadge({ status }: { status: DailyReportStatus }) {
  const config = PHASE1_STATUS_CONFIG[status] || {
    label: status,
    color: 'bg-gray-100 text-gray-700',
    icon: FileText,
  };

  return (
    <Badge variant="outline" className={cn('font-medium', config.color)}>
      {config.label}
    </Badge>
  );
}

// ============================================================================
// 子组件 - 今日任务提示
// ============================================================================

function TodayTaskReminder({ pendingAccounts }: { pendingAccounts: AdAccount[] }) {
  if (pendingAccounts.length === 0) {
    return (
      <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
        <CheckCircle2 className="h-5 w-5 text-green-600" />
        <div>
          <p className="text-sm font-medium text-green-800">今日日报已全部提交</p>
          <p className="text-xs text-green-600">所有账户的日报都已完成提交</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
      <AlertCircle className="h-5 w-5 text-amber-600" />
      <div className="flex-1">
        <p className="text-sm font-medium text-amber-800">
          还有 {pendingAccounts.length} 个账户待提交日报
        </p>
        <p className="text-xs text-amber-600 mt-0.5">
          {pendingAccounts
            .slice(0, 3)
            .map((a) => a.name)
            .join('、')}
          {pendingAccounts.length > 3 && ` 等 ${pendingAccounts.length} 个账户`}
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// 子组件 - 日报列表表格
// ============================================================================

interface ReportsTableProps {
  reports: DailyReport[];
  isLoading: boolean;
  onEdit: (report: DailyReport) => void;
  onDelete: (id: string) => void;
  onView: (report: DailyReport) => void;
}

function ReportsTable({ reports, isLoading, onEdit, onDelete, onView }: ReportsTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (reports.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 mx-auto text-gray-300 mb-4" />
        <p className="text-gray-500">暂无日报数据</p>
        <p className="text-sm text-gray-400 mt-1">点击上方"填写日报"开始提交</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">日期</TableHead>
          <TableHead>账户</TableHead>
          <TableHead className="text-right">消耗</TableHead>
          <TableHead className="text-right">进粉</TableHead>
          <TableHead className="text-right">单粉成本</TableHead>
          <TableHead>状态</TableHead>
          <TableHead className="w-[80px]">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {reports.map((report) => {
          const rawSpend =
            typeof report.raw_spend === 'object'
              ? (report.raw_spend?.amount ?? 0)
              : (report.raw_spend ?? 0);
          const followsCount = report.follows_count ?? 0;
          const costPerFollow = followsCount > 0 ? (rawSpend / followsCount).toFixed(2) : '-';
          const canEdit = report.status === 'raw_submitted';

          return (
            <TableRow key={report.id}>
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  {isToday(parseISO(report.report_date)) ? (
                    <span className="text-blue-600">今日</span>
                  ) : (
                    format(parseISO(report.report_date), 'MM/dd')
                  )}
                </div>
              </TableCell>
              <TableCell>
                <div>
                  <p className="font-medium text-gray-900">
                    {report.ad_account_name || `账户 #${report.ad_account_id}`}
                  </p>
                  {report.project_name && (
                    <p className="text-xs text-gray-500">{report.project_name}</p>
                  )}
                </div>
              </TableCell>
              <TableCell className="text-right font-mono">${rawSpend.toLocaleString()}</TableCell>
              <TableCell className="text-right font-mono">
                {followsCount.toLocaleString()}
              </TableCell>
              <TableCell className="text-right font-mono">
                {costPerFollow !== '-' ? `$${costPerFollow}` : '-'}
              </TableCell>
              <TableCell>
                <StatusBadge status={report.status} />
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onView(report)}>
                      <Eye className="h-4 w-4 mr-2" />
                      查看详情
                    </DropdownMenuItem>
                    {canEdit && (
                      <>
                        <DropdownMenuItem onClick={() => onEdit(report)}>
                          <Edit className="h-4 w-4 mr-2" />
                          编辑
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => onDelete(String(report.id))}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          删除
                        </DropdownMenuItem>
                      </>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

// ============================================================================
// 主组件
// ============================================================================

export function PitcherWorkbench() {
  // ========== State ==========
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingReport, setEditingReport] = useState<DailyReport | null>(null);
  const [dateFilter, setDateFilter] = useState<string>('');

  // ========== Data Fetching ==========
  const { data: reportsData, isLoading: isLoadingReports } = useDailyReports({
    page: 1,
    page_size: 50,
    sort_by: 'report_date',
    sort_order: 'desc',
    start_date: dateFilter || undefined,
    end_date: dateFilter || undefined,
  });

  const { data: stats } = useDailyReportStats();
  const { data: myAccounts = [], isLoading: isLoadingAccounts } = useMyAdAccounts();
  const { refreshAll } = useRefreshDailyReports();
  const deleteMutation = useDeleteDailyReport();

  // ========== Computed ==========
  const reports = reportsData?.items ?? [];
  const todayReports = reports.filter((r) => isToday(parseISO(r.report_date)));

  // 计算今日统计
  const todayStats = useMemo(() => {
    const todayData = todayReports;
    const totalSpend = todayData.reduce((sum, r) => {
      const spend = typeof r.raw_spend === 'object' ? r.raw_spend.amount : r.raw_spend;
      return sum + spend;
    }, 0);
    const totalFollows = todayData.reduce((sum, r) => sum + r.follows_count, 0);
    const avgCPL = totalFollows > 0 ? totalSpend / totalFollows : 0;

    return {
      totalSpend,
      totalFollows,
      avgCPL,
      reportCount: todayData.length,
    };
  }, [todayReports]);

  // 计算待提交账户 (今日未提交的账户)
  const pendingAccounts = useMemo(() => {
    const submittedAccountIds = new Set(todayReports.map((r) => r.ad_account_id));
    return myAccounts.filter((acc) => !submittedAccountIds.has(acc.id));
  }, [todayReports, myAccounts]);

  // ========== Handlers ==========
  const handleEdit = (report: DailyReport) => {
    setEditingReport(report);
    setIsFormOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这条日报吗？此操作不可撤销。')) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(id);
      toast.success('日报已删除');
    } catch {
      toast.error('删除失败');
    }
  };

  const handleView = (report: DailyReport) => {
    // TODO: 打开详情弹窗或跳转详情页
    console.log('View report:', report);
    toast.info(`查看日报 #${report.id}`);
  };

  const handleFormSuccess = () => {
    setIsFormOpen(false);
    setEditingReport(null);
    refreshAll();
    toast.success(editingReport ? '日报已更新' : '日报已提交');
  };

  const handleFormCancel = () => {
    setIsFormOpen(false);
    setEditingReport(null);
  };

  // ========== Render ==========
  return (
    <div className="min-h-screen bg-gray-50 -m-6 p-6 space-y-6">
      {/* ====== Header ====== */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">投手工作台</h1>
          <p className="text-sm text-gray-500 mt-1">
            {format(new Date(), 'yyyy年MM月dd日 EEEE', { locale: zhCN })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refreshAll()}
            disabled={isLoadingReports}
          >
            <RefreshCw className={cn('h-4 w-4 mr-2', isLoadingReports && 'animate-spin')} />
            刷新
          </Button>

          <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                填写日报
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingReport ? '编辑日报' : '填写日报'}</DialogTitle>
                <DialogDescription>
                  {editingReport
                    ? '修改日报数据，仅"已提交"状态的日报可以编辑'
                    : '填写今日广告投放数据，提交后进入审核流程'}
                </DialogDescription>
              </DialogHeader>
              <DailyReportForm
                report={
                  editingReport
                    ? {
                        id: editingReport.id,
                        report_date: editingReport.report_date,
                        ad_account_id: editingReport.ad_account_id,
                        raw_spend:
                          typeof editingReport.raw_spend === 'object'
                            ? editingReport.raw_spend.amount
                            : editingReport.raw_spend,
                        follows_count: editingReport.follows_count,
                        result_count: editingReport.result_count,
                        region: editingReport.region || '',
                        platform: editingReport.platform || '',
                        currency: editingReport.currency || 'USD',
                        campaign_name: editingReport.campaign_name || '',
                        ad_group_name: editingReport.ad_group_name || '',
                        ad_creative_name: editingReport.ad_creative_name || '',
                        impressions: editingReport.raw_impressions || 0,
                        clicks: editingReport.raw_clicks || 0,
                        notes: '',
                      }
                    : null
                }
                adAccounts={myAccounts}
                onSuccess={handleFormSuccess}
                onCancel={handleFormCancel}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* ====== 今日任务提示 ====== */}
      {!isLoadingAccounts && <TodayTaskReminder pendingAccounts={pendingAccounts} />}

      {/* ====== KPI Cards ====== */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="今日提交"
          value={todayStats.reportCount}
          subtitle={`共 ${myAccounts.length} 个账户`}
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="今日消耗"
          value={`$${todayStats.totalSpend.toLocaleString()}`}
          icon={DollarSign}
          color="amber"
        />
        <StatCard title="今日进粉" value={todayStats.totalFollows} icon={Users} color="green" />
        <StatCard
          title="平均单粉成本"
          value={todayStats.avgCPL > 0 ? `$${todayStats.avgCPL.toFixed(2)}` : '-'}
          icon={Target}
          color="purple"
        />
      </div>

      {/* ====== 状态统计 ====== */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <Card className="bg-white">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-blue-600">{stats.raw_submitted ?? 0}</p>
              <p className="text-sm text-gray-500">待审核</p>
            </CardContent>
          </Card>
          <Card className="bg-white">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-green-600">{stats.trend_ok ?? 0}</p>
              <p className="text-sm text-gray-500">趋势正常</p>
            </CardContent>
          </Card>
          <Card className="bg-white">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-emerald-600">{stats.final_confirmed ?? 0}</p>
              <p className="text-sm text-gray-500">已确认</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ====== 日报列表 ====== */}
      <Card className="bg-white shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">我的日报</CardTitle>
              <CardDescription>显示最近提交的日报记录</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="w-[160px]"
                placeholder="筛选日期"
              />
              {dateFilter && (
                <Button variant="ghost" size="sm" onClick={() => setDateFilter('')}>
                  清除
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ReportsTable
            reports={reports}
            isLoading={isLoadingReports}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onView={handleView}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export default PitcherWorkbench;
