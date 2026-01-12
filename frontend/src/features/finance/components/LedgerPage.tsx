/**
 * LedgerPage - 账本子页面
 *
 * TASK-FE-FIN-002: 账本子页面
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §6.5.1 (子页面)
 * - API_SOT.md v9.7 (GET /api/v1/ledger)
 * - MASTER.md v4.9 §2.4 (ceo, finance, admin 可访问)
 *
 * 功能:
 * - 显示资金流水记录
 * - 支持日期范围筛选
 * - 支持类型筛选（充值、消耗、红冲）
 * - 显示余额变化
 */

'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
  Book,
  Search,
  Calendar,
  RefreshCw,
  ArrowUpCircle,
  ArrowDownCircle,
  MinusCircle,
  Download,
  Filter,
} from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { useLedger } from '../hooks/useFinance';

// === 类型定义 ===

type LedgerType = 'all' | 'topup' | 'spend' | 'reversal';

interface LedgerFiltersState {
  type: LedgerType;
  search: string;
  startDate: string;
  endDate: string;
}

// === 配置 ===

const LEDGER_TYPE_CONFIG: Record<string, { label: string; icon: typeof ArrowUpCircle; color: string }> = {
  topup: { label: '充值', icon: ArrowUpCircle, color: 'text-green-600' },
  spend: { label: '消耗', icon: ArrowDownCircle, color: 'text-red-600' },
  reversal: { label: '红冲', icon: MinusCircle, color: 'text-orange-600' },
};

// === 辅助函数 ===

const formatMoney = (amount: number) => {
  const absAmount = Math.abs(amount);
  if (absAmount >= 10000) {
    return `${amount >= 0 ? '+' : '-'}¥${(absAmount / 10000).toFixed(2)} 万`;
  }
  return `${amount >= 0 ? '+' : '-'}¥${absAmount.toLocaleString()}`;
};

const formatDate = (dateString: string) => {
  return format(new Date(dateString), 'yyyy-MM-dd HH:mm', { locale: zhCN });
};

// === 子组件 ===

function LedgerFilters({
  filters,
  onChange,
  onReset,
}: {
  filters: LedgerFiltersState;
  onChange: (filters: LedgerFiltersState) => void;
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
        value={filters.type}
        onValueChange={(v) => onChange({ ...filters, type: v as LedgerType })}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="交易类型" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部类型</SelectItem>
          <SelectItem value="topup">充值</SelectItem>
          <SelectItem value="spend">消耗</SelectItem>
          <SelectItem value="reversal">红冲</SelectItem>
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

function LedgerTable({
  items,
  isLoading,
}: {
  items: Array<{
    id: string;
    type: string;
    amount: number;
    balance_after: number;
    description: string;
    account_name?: string;
    project_name?: string;
    created_at: string;
    ref_id?: string;
  }>;
  isLoading: boolean;
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
        <Book className="h-12 w-12 mb-4 opacity-50" />
        <p>暂无流水记录</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => {
        const config = LEDGER_TYPE_CONFIG[item.type] || LEDGER_TYPE_CONFIG.spend;
        const Icon = config.icon;
        const isPositive = item.amount >= 0;

        return (
          <div
            key={item.id}
            className="flex items-center gap-4 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className={`flex h-10 w-10 items-center justify-center rounded-full ${
              isPositive ? 'bg-green-100' : 'bg-red-100'
            }`}>
              <Icon className={`h-5 w-5 ${config.color}`} />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium truncate">{item.description}</span>
                <Badge variant="outline" className="text-xs">
                  {config.label}
                </Badge>
                {item.ref_id && (
                  <Badge variant="secondary" className="text-xs">
                    红冲
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                {item.account_name && <span>{item.account_name}</span>}
                {item.project_name && <span>{item.project_name}</span>}
                <span>{formatDate(item.created_at)}</span>
              </div>
            </div>

            <div className="text-right">
              <div className={`font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {formatMoney(item.amount)}
              </div>
              <div className="text-sm text-muted-foreground">
                余额: ¥{item.balance_after?.toLocaleString() ?? '-'}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// === 主组件 ===

export function LedgerPage() {
  const [filters, setFilters] = useState<LedgerFiltersState>({
    type: 'all',
    search: '',
    startDate: '',
    endDate: '',
  });
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // 获取数据
  const { data, isLoading, refetch, isRefetching } = useLedger({
    page,
    page_size: pageSize,
    type: filters.type !== 'all' ? filters.type : undefined,
    search: filters.search || undefined,
    start_date: filters.startDate || undefined,
    end_date: filters.endDate || undefined,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  const handleResetFilters = () => {
    setFilters({
      type: 'all',
      search: '',
      startDate: '',
      endDate: '',
    });
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100">
            <Book className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">账本</h1>
            <p className="text-sm text-muted-foreground">资金流水记录，不可删除只能红冲</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => refetch()} disabled={isRefetching}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      {/* Filters */}
      <LedgerFilters
        filters={filters}
        onChange={(f) => {
          setFilters(f);
          setPage(1);
        }}
        onReset={handleResetFilters}
      />

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>流水记录</span>
            <span className="text-sm font-normal text-muted-foreground">
              共 {total} 条记录
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LedgerTable items={items} isLoading={isLoading} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                第 {page} / {totalPages} 页
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default LedgerPage;
