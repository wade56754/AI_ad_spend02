/**
 * FinanceAnalysisDashboard - 财务分析仪表板
 *
 * 提供详细的财务分析视图，包括：
 * - 收支概览卡片
 * - 趋势图表
 * - 项目收益排行
 * - 渠道成本分析
 * - 利润率分析
 *
 * SoT References:
 * - BR-FIN.md v1.1 (财务规则)
 * - BR-PROFIT.md v1.2 (利润统计)
 * - MASTER.md v4.9 §2.4 (权限)
 *
 * @module features/finance/components
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  AlertTriangle,
  CheckCircle,
  Calendar,
  RefreshCw,
  Loader2,
  ChevronRight,
  BookOpen,
  Plus,
  Settings2,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import {
  useFundOverviewV2,
  useProfitOverviewV2,
  useProjectProfitsV2,
  useProfitTrendV2,
} from '../hooks/useFinance';
import { formatCurrency, formatPercent } from '@/lib/format';

// === 时间周期选项 ===
const PERIOD_OPTIONS = [
  { value: 'month', label: '本月' },
  { value: 'quarter', label: '本季度' },
  { value: 'year', label: '本年' },
];

// === 利润状态配置 ===
const PROFIT_STATUS_CONFIG = {
  healthy: { label: '健康', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  watch: { label: '关注', color: 'bg-yellow-100 text-yellow-800', icon: AlertTriangle },
  warning: { label: '警告', color: 'bg-red-100 text-red-800', icon: AlertTriangle },
  inactive: { label: '非活跃', color: 'bg-gray-100 text-gray-800', icon: Target },
};

export function FinanceAnalysisDashboard() {
  const [period, setPeriod] = useState<'month' | 'quarter' | 'year'>('month');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const queryClient = useQueryClient();

  // 获取数据
  const { data: fundOverview, isLoading: isLoadingFund, refetch: refetchFund } = useFundOverviewV2({ period });
  const { data: profitOverview, isLoading: isLoadingProfit, refetch: refetchProfit } = useProfitOverviewV2({ period: getCurrentPeriod() });
  const { data: projectProfits, isLoading: isLoadingProjects, refetch: refetchProjects } = useProjectProfitsV2({ sort_by: 'profit' });
  const { data: profitTrend, isLoading: isLoadingTrend, refetch: refetchTrend } = useProfitTrendV2({ granularity: 'week' });

  // 获取当前时间周期字符串
  function getCurrentPeriod() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([refetchFund(), refetchProfit(), refetchProjects(), refetchTrend()]);
    setIsRefreshing(false);
  };

  const isLoading = isLoadingFund || isLoadingProfit || isLoadingProjects || isLoadingTrend;

  // 从 V2 响应中提取数据
  const summary = fundOverview?.summary ?? {
    total_income: 0,
    total_expense: 0,
    outstanding: 0,
    available_balance: 0,
  };

  const profitSummary = profitOverview?.summary ?? {
    total_revenue: 0,
    total_cost: 0,
    total_profit: 0,
    avg_profit_rate: 0,
  };

  const changes = fundOverview?.changes ?? {};
  const profitChanges = profitOverview?.changes ?? {};

  const projects = projectProfits?.items ?? [];
  const trends = profitTrend?.series ?? [];

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100">
            <BarChart3 className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">财务分析</h1>
            <p className="text-sm text-gray-500">深度财务数据分析与可视化</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={(v) => setPeriod(v as typeof period)}>
            <SelectTrigger className="w-32">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PERIOD_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* 核心指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 总收入 */}
        <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="pt-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-500">总收入</p>
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-50">
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  </div>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(profitSummary.total_revenue)}
                </p>
                {changes.income_change_pct !== null && changes.income_change_pct !== undefined && (
                  <div className={`flex items-center text-sm ${changes.income_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {changes.income_change_pct >= 0 ? (
                      <ArrowUpRight className="h-4 w-4" />
                    ) : (
                      <ArrowDownRight className="h-4 w-4" />
                    )}
                    <span>{Math.abs(changes.income_change_pct).toFixed(1)}% 较上期</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 总成本 */}
        <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="pt-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-500">总成本</p>
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50">
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  </div>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(profitSummary.total_cost)}
                </p>
                {changes.expense_change_pct !== null && changes.expense_change_pct !== undefined && (
                  <div className={`flex items-center text-sm ${changes.expense_change_pct <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {changes.expense_change_pct <= 0 ? (
                      <ArrowDownRight className="h-4 w-4" />
                    ) : (
                      <ArrowUpRight className="h-4 w-4" />
                    )}
                    <span>{Math.abs(changes.expense_change_pct).toFixed(1)}% 较上期</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 总利润 */}
        <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="pt-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-500">总利润</p>
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-50">
                    <DollarSign className="h-4 w-4 text-purple-600" />
                  </div>
                </div>
                <p className={`text-2xl font-bold ${profitSummary.total_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(profitSummary.total_profit)}
                </p>
                {profitChanges.profit_change_pct !== null && profitChanges.profit_change_pct !== undefined && (
                  <div className={`flex items-center text-sm ${profitChanges.profit_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {profitChanges.profit_change_pct >= 0 ? (
                      <ArrowUpRight className="h-4 w-4" />
                    ) : (
                      <ArrowDownRight className="h-4 w-4" />
                    )}
                    <span>{Math.abs(profitChanges.profit_change_pct).toFixed(1)}% 较上期</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 平均利润率 */}
        <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="pt-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-500">平均利润率</p>
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50">
                    <Target className="h-4 w-4 text-blue-600" />
                  </div>
                </div>
                <p className={`text-2xl font-bold ${profitSummary.avg_profit_rate >= 0.15 ? 'text-green-600' : profitSummary.avg_profit_rate >= 0.1 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {formatPercent(profitSummary.avg_profit_rate, 1)}
                </p>
                <div className="flex items-center text-sm text-gray-500">
                  <span>行业平均 15%</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 分析标签页 */}
      <Tabs defaultValue="projects" className="space-y-4">
        <TabsList>
          <TabsTrigger value="projects" className="flex items-center gap-2">
            <PieChart className="h-4 w-4" />
            项目收益
          </TabsTrigger>
          <TabsTrigger value="trends" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            趋势分析
          </TabsTrigger>
          <TabsTrigger value="quick-actions" className="flex items-center gap-2">
            <Settings2 className="h-4 w-4" />
            快捷操作
          </TabsTrigger>
        </TabsList>

        {/* 项目收益排行 */}
        <TabsContent value="projects">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>项目收益排行</CardTitle>
                  <CardDescription>按利润排序的项目列表</CardDescription>
                </div>
                <Link href="/finance/profit">
                  <Button variant="ghost" size="sm">
                    查看详情 <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingProjects ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : projects.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <PieChart className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                  <p>暂无项目数据</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {projects.slice(0, 5).map((project, index) => {
                    const statusConfig = PROFIT_STATUS_CONFIG[project.profit_status as keyof typeof PROFIT_STATUS_CONFIG] ?? PROFIT_STATUS_CONFIG.inactive;
                    const StatusIcon = statusConfig.icon;
                    return (
                      <div
                        key={project.project_id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                      >
                        <div className="flex items-center gap-4">
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 font-bold text-gray-600">
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{project.project_name}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge className={statusConfig.color}>
                                <StatusIcon className="h-3 w-3 mr-1" />
                                {statusConfig.label}
                              </Badge>
                              <span className="text-xs text-gray-500">
                                进粉 {project.conversions ?? 0}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-bold ${(project.profit ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(project.profit ?? 0)}
                          </p>
                          <p className="text-sm text-gray-500">
                            利润率 {formatPercent(project.profit_rate ?? 0, 1)}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 趋势分析 */}
        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <CardTitle>利润趋势</CardTitle>
              <CardDescription>按周统计的收入、成本、利润趋势</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingTrend ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : trends.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <BarChart3 className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                  <p>暂无趋势数据</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {trends.map((item) => {
                    const maxValue = Math.max(...trends.map(t => Math.max(t.revenue ?? 0, t.cost ?? 0))) || 1;
                    return (
                      <div key={item.period} className="flex items-center gap-4">
                        <span className="w-20 text-sm text-gray-500">{item.period}</span>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-green-500 rounded-full"
                                style={{ width: `${((item.revenue ?? 0) / maxValue) * 100}%` }}
                              />
                            </div>
                            <span className="w-20 text-xs text-green-600 text-right">
                              {formatCurrency(item.revenue ?? 0)}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-red-400 rounded-full"
                                style={{ width: `${((item.cost ?? 0) / maxValue) * 100}%` }}
                              />
                            </div>
                            <span className="w-20 text-xs text-red-600 text-right">
                              {formatCurrency(item.cost ?? 0)}
                            </span>
                          </div>
                        </div>
                        <div className="w-24 text-right">
                          <span className={`font-bold ${(item.profit ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(item.profit ?? 0)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                  <div className="flex items-center justify-center gap-6 pt-4 border-t">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full" />
                      <span className="text-sm text-gray-500">收入</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-400 rounded-full" />
                      <span className="text-sm text-gray-500">成本</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 快捷操作 */}
        <TabsContent value="quick-actions">
          <Card>
            <CardHeader>
              <CardTitle>财务快捷操作</CardTitle>
              <CardDescription>常用的财务管理功能入口</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                <Link href="/ledger">
                  <Button variant="outline" className="w-full h-auto py-6 flex flex-col items-center gap-3">
                    <BookOpen className="h-8 w-8 text-emerald-600" />
                    <div className="text-center">
                      <p className="font-medium">财务总账</p>
                      <p className="text-xs text-gray-500">查看/录入交易</p>
                    </div>
                  </Button>
                </Link>
                <Link href="/topups">
                  <Button variant="outline" className="w-full h-auto py-6 flex flex-col items-center gap-3">
                    <Plus className="h-8 w-8 text-blue-600" />
                    <div className="text-center">
                      <p className="font-medium">申请充值</p>
                      <p className="text-xs text-gray-500">创建充值申请</p>
                    </div>
                  </Button>
                </Link>
                <Link href="/finance/fund">
                  <Button variant="outline" className="w-full h-auto py-6 flex flex-col items-center gap-3">
                    <DollarSign className="h-8 w-8 text-green-600" />
                    <div className="text-center">
                      <p className="font-medium">资金总览</p>
                      <p className="text-xs text-gray-500">余额与应收</p>
                    </div>
                  </Button>
                </Link>
                <Link href="/finance/profit">
                  <Button variant="outline" className="w-full h-auto py-6 flex flex-col items-center gap-3">
                    <PieChart className="h-8 w-8 text-purple-600" />
                    <div className="text-center">
                      <p className="font-medium">项目盈亏</p>
                      <p className="text-xs text-gray-500">收益分析</p>
                    </div>
                  </Button>
                </Link>
                <Link href="/reconciliation">
                  <Button variant="outline" className="w-full h-auto py-6 flex flex-col items-center gap-3">
                    <CheckCircle className="h-8 w-8 text-teal-600" />
                    <div className="text-center">
                      <p className="font-medium">对账管理</p>
                      <p className="text-xs text-gray-500">核对差异</p>
                    </div>
                  </Button>
                </Link>
                <Link href="/settlements">
                  <Button variant="outline" className="w-full h-auto py-6 flex flex-col items-center gap-3">
                    <BarChart3 className="h-8 w-8 text-orange-600" />
                    <div className="text-center">
                      <p className="font-medium">结算管理</p>
                      <p className="text-xs text-gray-500">月度结算</p>
                    </div>
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default FinanceAnalysisDashboard;
