'use client';

/**
 * Project Dashboard Component
 * TASK-PRJ-004
 *
 * 项目仪表盘: KPI 卡片 + 趋势图表 + 账户表现
 */

import React from 'react';
import {
  DollarSign,
  Users,
  Target,
  TrendingUp,
  TrendingDown,
  Percent,
  RefreshCw,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { useProjectDashboard } from '../hooks';
import type { ProjectDashboard as DashboardData, AccountPerformance } from '../types';

interface ProjectDashboardProps {
  projectId: number;
  budget?: number;
}

// 格式化金额
function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '¥0';
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// 格式化百分比
function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '0%';
  return `${value.toFixed(1)}%`;
}

// KPI 卡片组件
function KPICard({
  title,
  value,
  icon: Icon,
  trend,
  trendLabel,
  color,
}: {
  title: string;
  value: string;
  icon: React.ElementType;
  trend?: number;
  trendLabel?: string;
  color: string;
}) {
  const isPositive = trend !== undefined && trend >= 0;

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {trend !== undefined && (
              <div className="flex items-center mt-2 text-sm">
                {isPositive ? (
                  <TrendingUp className="w-4 h-4 text-emerald-500 mr-1" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                )}
                <span className={isPositive ? 'text-emerald-500' : 'text-red-500'}>
                  {isPositive ? '+' : ''}
                  {trend.toFixed(1)}%
                </span>
                {trendLabel && <span className="text-muted-foreground ml-1">{trendLabel}</span>}
              </div>
            )}
          </div>
          <div className={`p-3 rounded-full ${color}`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// 账户状态 Badge
function AccountStatusBadge({ status }: { status: string }) {
  const config: Record<
    string,
    { variant: 'default' | 'success' | 'warning' | 'destructive'; label: string }
  > = {
    active: { variant: 'success', label: '活跃' },
    paused: { variant: 'warning', label: '暂停' },
    suspended: { variant: 'destructive', label: '封禁' },
    dead: { variant: 'destructive', label: '死号' },
  };

  const { variant, label } = config[status] || { variant: 'default', label: status };

  return <Badge variant={variant}>{label}</Badge>;
}

// 加载骨架
function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-32 mb-2" />
              <Skeleton className="h-4 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Chart */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[200px] w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

export function ProjectDashboard({ projectId, budget }: ProjectDashboardProps) {
  const { data, isLoading, error, refetch, isFetching } = useProjectDashboard(projectId, {
    days: 30,
  });

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-10 text-center">
          <p className="text-destructive mb-4">加载仪表盘数据失败</p>
          <Button variant="outline" onClick={() => refetch()}>
            重试
          </Button>
        </CardContent>
      </Card>
    );
  }

  const dashboard = data?.data;
  if (!dashboard) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-muted-foreground">暂无数据</CardContent>
      </Card>
    );
  }

  // 格式化趋势图数据
  const trendData = dashboard.daily_trend.map((item) => ({
    date: item.date.slice(5), // MM-DD
    消耗: Number(item.spend),
    进粉: item.follows,
    CPL: item.cpl ? Number(item.cpl) : 0,
  }));

  return (
    <div className="space-y-6">
      {/* 刷新按钮 */}
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
          刷新数据
        </Button>
      </div>

      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="总消耗"
          value={formatCurrency(dashboard.total_spend)}
          icon={DollarSign}
          color="bg-blue-500"
        />
        <KPICard
          title="总进粉"
          value={dashboard.total_follows.toLocaleString()}
          icon={Users}
          color="bg-emerald-500"
        />
        <KPICard
          title="平均 CPL"
          value={dashboard.avg_cpl ? formatCurrency(dashboard.avg_cpl) : '-'}
          icon={Target}
          color="bg-purple-500"
        />
        <KPICard
          title="预算使用率"
          value={formatPercent(dashboard.budget_usage_percent)}
          icon={Percent}
          color={dashboard.budget_usage_percent > 80 ? 'bg-red-500' : 'bg-orange-500'}
        />
      </div>

      {/* 趋势图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 消耗趋势 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">消耗趋势 (近 30 天)</CardTitle>
          </CardHeader>
          <CardContent>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number) => [`¥${value.toFixed(2)}`, '消耗']}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="消耗"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[280px] flex items-center justify-center text-muted-foreground">
                暂无趋势数据
              </div>
            )}
          </CardContent>
        </Card>

        {/* 进粉趋势 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">进粉趋势 (近 30 天)</CardTitle>
          </CardHeader>
          <CardContent>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip labelFormatter={(label) => `日期: ${label}`} />
                  <Legend />
                  <Bar dataKey="进粉" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[280px] flex items-center justify-center text-muted-foreground">
                暂无趋势数据
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 账户表现 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">账户表现排行</CardTitle>
        </CardHeader>
        <CardContent>
          {dashboard.account_performance.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>账户名称</TableHead>
                  <TableHead>平台</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">消耗</TableHead>
                  <TableHead className="text-right">进粉</TableHead>
                  <TableHead className="text-right">CPL</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboard.account_performance.map((account: AccountPerformance) => (
                  <TableRow key={account.account_id}>
                    <TableCell className="font-medium">{account.account_name}</TableCell>
                    <TableCell>{account.platform || '-'}</TableCell>
                    <TableCell>
                      <AccountStatusBadge status={account.status} />
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(account.spend)}</TableCell>
                    <TableCell className="text-right">{account.follows.toLocaleString()}</TableCell>
                    <TableCell className="text-right">
                      {account.cpl ? formatCurrency(account.cpl) : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="py-10 text-center text-muted-foreground">暂无账户数据</div>
          )}
        </CardContent>
      </Card>

      {/* 统计周期 */}
      {dashboard.period_start && dashboard.period_end && (
        <p className="text-sm text-muted-foreground text-center">
          统计周期: {dashboard.period_start} 至 {dashboard.period_end}
        </p>
      )}
    </div>
  );
}

export default ProjectDashboard;
