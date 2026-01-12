/**
 * ReconciliationPage - 对账子页面
 *
 * TASK-FE-FIN-003: 对账子页面
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §6.5.1 (子页面)
 * - API_SOT.md v9.7 (GET /api/v1/reconciliation)
 * - MASTER.md v4.9 §2.4 (ceo, finance, admin 可访问)
 *
 * 功能:
 * - 显示对账记录
 * - 支持日期范围筛选
 * - 高亮差异数据
 * - 支持对账操作
 */

'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  FileCheck,
  Search,
  Calendar,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  Filter,
  Eye,
} from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { toast } from 'sonner';

// === 类型定义 ===

type ReconciliationStatus = 'all' | 'pending' | 'matched' | 'mismatched' | 'resolved';

interface ReconciliationFiltersState {
  status: ReconciliationStatus;
  search: string;
  startDate: string;
  endDate: string;
}

interface ReconciliationItem {
  id: string;
  date: string;
  account_name: string;
  project_name: string;
  platform_spend: number;
  reported_spend: number;
  difference: number;
  difference_rate: number;
  status: string;
  resolved_at?: string;
  resolved_by?: string;
  notes?: string;
}

// === 配置 ===

const STATUS_CONFIG: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  pending: { label: '待对账', variant: 'secondary' },
  matched: { label: '已匹配', variant: 'default' },
  mismatched: { label: '有差异', variant: 'destructive' },
  resolved: { label: '已解决', variant: 'outline' },
};

// === 辅助函数 ===

const formatMoney = (amount: number) => {
  const absAmount = Math.abs(amount);
  if (absAmount >= 10000) {
    return `¥${(absAmount / 10000).toFixed(2)} 万`;
  }
  return `¥${absAmount.toLocaleString()}`;
};

const formatDate = (dateString: string) => {
  return format(new Date(dateString), 'yyyy-MM-dd', { locale: zhCN });
};

// === Mock 数据 (实际应从 API 获取) ===

const MOCK_DATA: ReconciliationItem[] = [
  {
    id: '1',
    date: '2026-01-05',
    account_name: '抖音-主账户A',
    project_name: '项目Alpha',
    platform_spend: 125000,
    reported_spend: 125000,
    difference: 0,
    difference_rate: 0,
    status: 'matched',
  },
  {
    id: '2',
    date: '2026-01-05',
    account_name: '头条-账户B',
    project_name: '项目Beta',
    platform_spend: 85000,
    reported_spend: 83500,
    difference: 1500,
    difference_rate: 1.76,
    status: 'mismatched',
    notes: '平台扣费时间差',
  },
  {
    id: '3',
    date: '2026-01-04',
    account_name: '快手-账户C',
    project_name: '项目Gamma',
    platform_spend: 45000,
    reported_spend: 45000,
    difference: 0,
    difference_rate: 0,
    status: 'matched',
  },
  {
    id: '4',
    date: '2026-01-04',
    account_name: '抖音-账户D',
    project_name: '项目Delta',
    platform_spend: 0,
    reported_spend: 0,
    difference: 0,
    difference_rate: 0,
    status: 'pending',
  },
];

// === 子组件 ===

function ReconciliationFilters({
  filters,
  onChange,
  onReset,
}: {
  filters: ReconciliationFiltersState;
  onChange: (filters: ReconciliationFiltersState) => void;
  onReset: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">筛选</span>
      </div>

      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="搜索账户、项目..."
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="pl-10"
        />
      </div>

      <Select
        value={filters.status}
        onValueChange={(v) => onChange({ ...filters, status: v as ReconciliationStatus })}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="对账状态" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部状态</SelectItem>
          <SelectItem value="pending">待对账</SelectItem>
          <SelectItem value="matched">已匹配</SelectItem>
          <SelectItem value="mismatched">有差异</SelectItem>
          <SelectItem value="resolved">已解决</SelectItem>
        </SelectContent>
      </Select>

      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 text-muted-foreground" />
        <Input
          type="date"
          value={filters.startDate}
          onChange={(e) => onChange({ ...filters, startDate: e.target.value })}
          className="w-[140px]"
        />
        <span className="text-muted-foreground">至</span>
        <Input
          type="date"
          value={filters.endDate}
          onChange={(e) => onChange({ ...filters, endDate: e.target.value })}
          className="w-[140px]"
        />
      </div>

      <Button variant="outline" size="sm" onClick={onReset}>
        重置
      </Button>
    </div>
  );
}

function ReconciliationTable({
  items,
  isLoading,
  onResolve,
}: {
  items: ReconciliationItem[];
  isLoading: boolean;
  onResolve: (item: ReconciliationItem) => void;
}) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-6 w-24" />
          </div>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <FileCheck className="h-12 w-12 mb-4 opacity-50" />
        <p>暂无对账记录</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">账户/项目</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">平台消耗</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">日报消耗</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">差异</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">状态</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map((item) => {
            const statusConfig = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending;
            const hasDifference = item.difference !== 0;

            return (
              <tr key={item.id} className={`hover:bg-gray-50 ${hasDifference ? 'bg-red-50/50' : ''}`}>
                <td className="px-4 py-3 text-sm">{formatDate(item.date)}</td>
                <td className="px-4 py-3">
                  <div className="text-sm font-medium">{item.account_name}</div>
                  <div className="text-xs text-muted-foreground">{item.project_name}</div>
                </td>
                <td className="px-4 py-3 text-right text-sm font-medium">
                  {formatMoney(item.platform_spend)}
                </td>
                <td className="px-4 py-3 text-right text-sm font-medium">
                  {formatMoney(item.reported_spend)}
                </td>
                <td className="px-4 py-3 text-right">
                  {hasDifference ? (
                    <div className="flex items-center justify-end gap-1">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <span className="text-sm font-medium text-red-600">
                        {item.difference > 0 ? '+' : ''}{formatMoney(item.difference)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        ({item.difference_rate.toFixed(2)}%)
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-green-600 flex items-center justify-end gap-1">
                      <CheckCircle className="h-4 w-4" />
                      一致
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                    {item.status === 'mismatched' && (
                      <Button variant="outline" size="sm" onClick={() => onResolve(item)}>
                        解决
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// === 主组件 ===

export function ReconciliationPage() {
  const [filters, setFilters] = useState<ReconciliationFiltersState>({
    status: 'all',
    search: '',
    startDate: '',
    endDate: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [resolveItem, setResolveItem] = useState<ReconciliationItem | null>(null);

  // TODO: 替换为真实 API 调用
  const items = MOCK_DATA.filter((item) => {
    if (filters.status !== 'all' && item.status !== filters.status) return false;
    if (filters.search) {
      const search = filters.search.toLowerCase();
      if (!item.account_name.toLowerCase().includes(search) &&
          !item.project_name.toLowerCase().includes(search)) {
        return false;
      }
    }
    return true;
  });

  const handleResetFilters = () => {
    setFilters({
      status: 'all',
      search: '',
      startDate: '',
      endDate: '',
    });
  };

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1000);
  };

  const handleResolve = () => {
    if (!resolveItem) return;
    toast.success(`对账差异已标记为解决`);
    setResolveItem(null);
  };

  // 统计
  const stats = {
    total: items.length,
    matched: items.filter((i) => i.status === 'matched').length,
    mismatched: items.filter((i) => i.status === 'mismatched').length,
    pending: items.filter((i) => i.status === 'pending').length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100">
            <FileCheck className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">对账管理</h1>
            <p className="text-sm text-muted-foreground">平台消耗与日报消耗对比</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-sm text-muted-foreground">总记录</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-green-600">{stats.matched}</div>
            <div className="text-sm text-muted-foreground">已匹配</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-red-600">{stats.mismatched}</div>
            <div className="text-sm text-muted-foreground">有差异</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-gray-600">{stats.pending}</div>
            <div className="text-sm text-muted-foreground">待对账</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <ReconciliationFilters
        filters={filters}
        onChange={setFilters}
        onReset={handleResetFilters}
      />

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>对账记录</CardTitle>
        </CardHeader>
        <CardContent>
          <ReconciliationTable
            items={items}
            isLoading={isLoading}
            onResolve={setResolveItem}
          />
        </CardContent>
      </Card>

      {/* Resolve Dialog */}
      <AlertDialog open={!!resolveItem} onOpenChange={() => setResolveItem(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>解决对账差异</AlertDialogTitle>
            <AlertDialogDescription>
              确认要将此对账差异标记为已解决吗？
              {resolveItem && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>账户</span>
                    <span className="font-medium">{resolveItem.account_name}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>差异金额</span>
                    <span className="font-medium text-red-600">
                      {formatMoney(resolveItem.difference)}
                    </span>
                  </div>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleResolve}>确认解决</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default ReconciliationPage;
