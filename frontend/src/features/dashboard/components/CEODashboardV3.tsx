/**
 * CEO Dashboard V3 Component
 *
 * SoT: CLAUDE_CLI_TASK_CEO_DASHBOARD_REFACTOR_V3.md
 *
 * Core Formula: Gross Profit = Revenue - Cost (No handling fee!)
 *
 * Sections:
 * 1. Company Cash Status
 * 2. Profit Overview (gross profit = revenue - cost)
 * 3. Project Balance
 * 4. Action Items
 * 5. Project Profit Ranking
 * 6. Trend Chart
 */

'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Users,
  BarChart3,
  AlertTriangle,
  Clock,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import {
  useCeoV3DashboardData,
  useCeoV3ProjectBalance,
  useCeoV3ActionItems,
  useRefreshCeoV3Dashboard,
} from '../hooks';

// ============ Helper Functions ============

function formatCurrency(amount: number, currency: string = 'USD'): string {
  if (currency === 'USD') {
    return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `${currency} ${amount.toLocaleString()}`;
}

function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
}

function getProfitStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-500';
    case 'warning':
      return 'bg-yellow-500';
    case 'danger':
      return 'bg-orange-500';
    case 'loss':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
}

function getProfitStatusBadge(status: string): React.ReactNode {
  const colors: Record<string, string> = {
    healthy: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-orange-100 text-orange-800',
    loss: 'bg-red-100 text-red-800',
    no_revenue: 'bg-gray-100 text-gray-600',
  };
  const labels: Record<string, string> = {
    healthy: '健康',
    warning: '警告',
    danger: '危险',
    loss: '亏损',
    no_revenue: '无收款',
  };
  return (
    <Badge className={colors[status] || 'bg-gray-100 text-gray-800'}>
      {labels[status] || status}
    </Badge>
  );
}

/**
 * 格式化利润率，处理 null 值
 */
function formatProfitRate(rate: number | null | undefined): string {
  if (rate === null || rate === undefined) {
    return '--';
  }
  return `${rate.toFixed(1)}%`;
}

/**
 * 获取结算模式标签
 */
function getPricingLabel(pricing?: { type: string; note?: string }): string {
  if (!pricing) return '按粉';
  switch (pricing.type) {
    case 'markup':
      return '服务费';
    case 'tiered':
      return '阶梯';
    case 'fixed':
    default:
      return '按粉';
  }
}

function getBalanceStatusBadge(status: string, label: string): React.ReactNode {
  const colors: Record<string, string> = {
    prepaid: 'bg-green-100 text-green-800',
    pending_refund: 'bg-yellow-100 text-yellow-800',
    refunded: 'bg-blue-100 text-blue-800',
    settled: 'bg-gray-100 text-gray-800',
    need_topup: 'bg-red-100 text-red-800',
  };
  return (
    <Badge className={colors[status] || 'bg-gray-100 text-gray-800'}>
      {label}
    </Badge>
  );
}

// ============ Period Selector ============

function PeriodSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const now = new Date();
  const periods = [];
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const period = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const label = d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' });
    periods.push({ value: period, label });
  }

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[180px]">
        <Calendar className="mr-2 h-4 w-4" />
        <SelectValue placeholder="Select period" />
      </SelectTrigger>
      <SelectContent>
        {periods.map((p) => (
          <SelectItem key={p.value} value={p.value}>
            {p.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

// ============ Stat Card Component ============

function StatCard({
  title,
  value,
  subtitle,
  change,
  icon,
  color = 'blue',
}: {
  title: string;
  value: string;
  subtitle?: string;
  change?: number;
  icon: React.ReactNode;
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red';
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {subtitle && (
              <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
            )}
            {change !== undefined && (
              <div className="flex items-center mt-2">
                {change >= 0 ? (
                  <ArrowUpRight className="h-4 w-4 text-green-500" />
                ) : (
                  <ArrowDownRight className="h-4 w-4 text-red-500" />
                )}
                <span
                  className={`text-sm font-medium ${
                    change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatPercent(change)}
                </span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============ Main Component ============

export function CEODashboardV3() {
  // State
  const [period, setPeriod] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  // Data fetching
  const { overview, projectRanking, trend, isLoading, isError, error } =
    useCeoV3DashboardData(period);
  const { data: projectBalance, isLoading: isBalanceLoading } =
    useCeoV3ProjectBalance(period);
  const { data: actionItems, isLoading: isActionsLoading } =
    useCeoV3ActionItems(period);
  const { refreshAll } = useRefreshCeoV3Dashboard();

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-9 w-48" />
          <Skeleton className="h-10 w-40" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">加载仪表盘失败</h2>
        <p className="text-muted-foreground mb-4">{error?.message || '未知错误'}</p>
        <Button onClick={() => refreshAll()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          重试
        </Button>
      </div>
    );
  }

  const cash = overview?.cash_status;
  const profit = overview?.profit_summary;
  const balanceSummary = overview?.project_balance_summary;
  const actions = overview?.action_items;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">CEO 驾驶舱</h1>
          <p className="text-muted-foreground mt-1">
            公式: 毛利 = 收款 - 消耗（不含手续费）
          </p>
        </div>
        <div className="flex items-center gap-4">
          <PeriodSelector value={period} onChange={setPeriod} />
          <Button variant="outline" onClick={() => refreshAll()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* Section 1: Company Cash Status */}
      <section>
        <h2 className="text-xl font-semibold mb-4">公司现金状况</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="期末余额"
            value={formatCurrency(cash?.closing_balance || 0)}
            change={cash?.balance_change_pct}
            icon={<DollarSign className="h-6 w-6" />}
            color="blue"
          />
          <StatCard
            title="总收入"
            value={formatCurrency(cash?.total_income || 0)}
            subtitle="甲方打款"
            icon={<TrendingUp className="h-6 w-6" />}
            color="green"
          />
          <StatCard
            title="总支出"
            value={formatCurrency(cash?.total_expense || 0)}
            subtitle="渠道充值 + 运营成本"
            icon={<TrendingDown className="h-6 w-6" />}
            color="orange"
          />
          <StatCard
            title="资金周转"
            value={`${cash?.runway_days || 0} 天`}
            subtitle="仅广告业务"
            icon={<Clock className="h-6 w-6" />}
            color="purple"
          />
        </div>
      </section>

      {/* Section 2: Profit Overview - 本月数据 */}
      <section>
        <h2 className="text-xl font-semibold mb-4">盈利概览 <span className="text-sm font-normal text-muted-foreground">(本月)</span></h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="本月收款"
            value={formatCurrency(profit?.total_revenue || 0)}
            subtitle={`${profit?.total_conversions?.toLocaleString() || 0} 个转化`}
            icon={<DollarSign className="h-6 w-6" />}
            color="green"
          />
          <StatCard
            title="本月消耗"
            value={formatCurrency(profit?.total_cost || 0)}
            subtitle="= 实际消耗（不含手续费）"
            icon={<Wallet className="h-6 w-6" />}
            color="orange"
          />
          <StatCard
            title="毛利"
            value={formatCurrency(profit?.total_profit || 0)}
            subtitle={`${formatProfitRate(profit?.profit_rate_pct)} 利润率`}
            icon={<TrendingUp className="h-6 w-6" />}
            color={profit?.profit_status === 'loss' ? 'red' : profit?.profit_status === 'healthy' ? 'green' : profit?.profit_status === 'no_revenue' ? 'purple' : 'orange'}
          />
          <StatCard
            title="单转化成本"
            value={`$${(profit?.avg_cpl || 0).toFixed(2)}`}
            subtitle="CPL"
            icon={<Users className="h-6 w-6" />}
            color="purple"
          />
        </div>
      </section>

      {/* Section 3: Project Balance - 累计数据 */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">项目余额 <span className="text-sm font-normal text-muted-foreground">(累计)</span></h2>
          <Link href="/projects">
            <Button variant="ghost" size="sm">
              查看全部
              <ArrowUpRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="pt-6">
            {isBalanceLoading ? (
              <Skeleton className="h-48" />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>项目</TableHead>
                    <TableHead className="text-right">累计收款</TableHead>
                    <TableHead className="text-right">累计消耗</TableHead>
                    <TableHead className="text-right">余额</TableHead>
                    <TableHead>状态</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {projectBalance?.items?.slice(0, 5).map((item) => (
                    <TableRow key={item.project_id}>
                      <TableCell className="font-medium">{item.project_name}</TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(item.cumulative_revenue)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(item.cumulative_cost)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(item.balance)}
                      </TableCell>
                      <TableCell>
                        {getBalanceStatusBadge(item.status, item.status_label)}
                      </TableCell>
                    </TableRow>
                  )) || (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        暂无数据
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
            {projectBalance?.totals && (
              <div className="mt-4 pt-4 border-t flex justify-end gap-8">
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">总收款</p>
                  <p className="font-semibold">
                    {formatCurrency(projectBalance.totals.cumulative_revenue)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">总消耗</p>
                  <p className="font-semibold">
                    {formatCurrency(projectBalance.totals.cumulative_cost)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">总余额</p>
                  <p className="font-bold text-lg">
                    {formatCurrency(projectBalance.totals.total_balance)}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Section 4: Action Items */}
      {((actions?.abnormal_projects_count ?? 0) > 0 || (actions?.pending_reports_count ?? 0) > 0 || (actions?.pending_refunds_count ?? 0) > 0) && (
        <section>
          <h2 className="text-xl font-semibold mb-4">待办事项</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(actions?.abnormal_projects_count ?? 0) > 0 && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                    <div>
                      <p className="text-2xl font-bold">{actions?.abnormal_projects_count ?? 0}</p>
                      <p className="text-sm text-muted-foreground">异常项目</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            {(actions?.pending_reports_count ?? 0) > 0 && (
              <Card className="border-yellow-200 bg-yellow-50">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Clock className="h-8 w-8 text-yellow-600" />
                    <div>
                      <p className="text-2xl font-bold">{actions?.pending_reports_count ?? 0}</p>
                      <p className="text-sm text-muted-foreground">待审核日报</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            {(actions?.pending_refunds_count ?? 0) > 0 && (
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Wallet className="h-8 w-8 text-blue-600" />
                    <div>
                      <p className="text-2xl font-bold">{actions?.pending_refunds_count ?? 0}</p>
                      <p className="text-sm text-muted-foreground">待退款项目</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </section>
      )}

      {/* Section 5: Project Profit Ranking */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">项目利润排名</h2>
          <Link href="/projects?sort=profit">
            <Button variant="ghost" size="sm">
              查看全部
              <ArrowUpRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>结算模式</TableHead>
                  <TableHead className="text-right">转化数</TableHead>
                  <TableHead className="text-right">收款</TableHead>
                  <TableHead className="text-right">消耗</TableHead>
                  <TableHead className="text-right">毛利</TableHead>
                  <TableHead className="text-right">利润率</TableHead>
                  <TableHead>状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projectRanking?.items?.map((item) => (
                  <TableRow key={item.project_id}>
                    <TableCell>
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold ${getProfitStatusColor(
                          item.profit_status
                        )}`}
                      >
                        {item.rank}
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">{item.project_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {getPricingLabel(item.pricing)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {item.metrics.conversions?.toLocaleString() || '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(item.metrics.revenue)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(item.metrics.cost)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(item.metrics.profit)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatProfitRate(item.metrics.profit_rate_pct)}
                    </TableCell>
                    <TableCell>{getProfitStatusBadge(item.profit_status)}</TableCell>
                  </TableRow>
                )) || (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground">
                      暂无数据
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
            {projectRanking?.summary && (
              <div className="mt-4 pt-4 border-t grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">项目总数</p>
                  <p className="font-semibold">{projectRanking.summary.total_projects}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">健康</p>
                  <p className="font-semibold text-green-600">
                    {projectRanking.summary.healthy_count}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">警告/危险</p>
                  <p className="font-semibold text-orange-600">
                    {projectRanking.summary.warning_count + projectRanking.summary.danger_count}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">总毛利</p>
                  <p className="font-bold">{formatCurrency(projectRanking.summary.total_profit)}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Section 6: Trend Chart */}
      <section>
        <h2 className="text-xl font-semibold mb-4">趋势</h2>
        <Card>
          <CardContent className="pt-6">
            {trend?.items && trend.items.length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Simple summary stats from trend data */}
                  {(() => {
                    const totalRevenue = trend.items.reduce((sum, t) => sum + t.revenue, 0);
                    const totalSpend = trend.items.reduce((sum, t) => sum + t.spend, 0);
                    const totalProfit = trend.items.reduce((sum, t) => sum + t.profit, 0);
                    return (
                      <>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                          <p className="text-sm text-muted-foreground">周期收款</p>
                          <p className="text-xl font-bold text-green-600">
                            {formatCurrency(totalRevenue)}
                          </p>
                        </div>
                        <div className="text-center p-4 bg-orange-50 rounded-lg">
                          <p className="text-sm text-muted-foreground">周期消耗</p>
                          <p className="text-xl font-bold text-orange-600">
                            {formatCurrency(totalSpend)}
                          </p>
                        </div>
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                          <p className="text-sm text-muted-foreground">周期毛利</p>
                          <p className="text-xl font-bold text-blue-600">
                            {formatCurrency(totalProfit)}
                          </p>
                        </div>
                      </>
                    );
                  })()}
                </div>
                <p className="text-sm text-muted-foreground text-center">
                  {trend.period} 共 {trend.items.length} 个数据点（{trend.granularity === 'daily' ? '按日' : trend.granularity}）
                </p>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>该周期暂无趋势数据</p>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <div className="text-center text-sm text-muted-foreground pb-8">
        <p>
          生成时间: {overview?.generated_at ? new Date(overview.generated_at).toLocaleString('zh-CN') : '暂无'} |
          公式版本: {overview?.formula_version || 'v3'} |
          {overview?.formula_note || '毛利 = 收款 - 消耗（不含手续费）'}
        </p>
      </div>
    </div>
  );
}

export default CEODashboardV3;
