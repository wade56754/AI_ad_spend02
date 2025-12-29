'use client';

/**
 * Finance Overview Page Component
 *
 * Route: /finance
 * Purpose: Financial dashboard with overview, trends, and quick actions
 * SoT 对齐: LEDGER_SOT.md v1.1, BUSINESS_RULES.md v3.2
 *
 * 使用真实后端 API 获取数据
 */

import React, { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  CreditCard,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  ChevronRight,
  PieChart,
  BarChart3,
  FileText,
  Plus,
  Loader2
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import {
  useFundOverview,
  useProfitTrend,
  useChannelDistribution,
  useFundAlerts,
} from '../hooks/useFinance';

// 格式化金额
const formatMoney = (amount: number | undefined | null) => {
  const num = Number(amount) || 0;
  if (Math.abs(num) >= 10000) {
    return `¥${(num / 10000).toFixed(2)} 万`;
  }
  return `¥${num.toLocaleString()}`;
};

// 待办类型图标和颜色
const todoConfig = {
  topup: { icon: CreditCard, color: 'text-blue-600', bg: 'bg-blue-100' },
  settlement: { icon: FileText, color: 'text-purple-600', bg: 'bg-purple-100' },
  reconciliation: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100' },
  alert: { icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-100' },
};

// 优先级颜色
const priorityColors = {
  high: 'bg-red-100 text-red-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-gray-100 text-gray-800',
};

export function FinancePage() {
  const queryClient = useQueryClient();

  // 获取真实数据
  const { data: fundOverview, isLoading: isLoadingOverview, refetch: refetchOverview } = useFundOverview();
  const { data: profitTrend, isLoading: isLoadingTrend, refetch: refetchTrend } = useProfitTrend({ granularity: 'day' });
  const { data: channelDistribution, isLoading: isLoadingChannels, refetch: refetchChannels } = useChannelDistribution();
  const { data: fundAlerts, isLoading: isLoadingAlerts, refetch: refetchAlerts } = useFundAlerts();

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([
      refetchOverview(),
      refetchTrend(),
      refetchChannels(),
      refetchAlerts(),
    ]);
    setIsRefreshing(false);
  };

  // 计算概览数据 (从真实数据或默认值)
  const overview = {
    total_topup: fundOverview?.total_topup ?? 0,      // 累计充值
    total_spend: fundOverview?.total_spend ?? 0,       // 累计消耗
    current_balance: fundOverview?.current_balance ?? 0, // 当前余额
    total_receivable: fundOverview?.total_receivable ?? 0, // 应收款
    total_received: fundOverview?.total_received ?? 0,   // 累计回款
    fund_occupied: fundOverview?.fund_occupied ?? 0,     // 资金占用
    occupy_rate: fundOverview?.occupy_rate ?? 0,         // 资金占用率
    pending_count: fundOverview?.pending_receivable_count ?? 0, // 待收款笔数
  };

  // 转换趋势数据格式 - 添加防护性检查
  const trends = (profitTrend ?? []).map(item => ({
    date: (item.date ?? '').slice(5) || '未知', // 取 MM-DD 部分
    revenue: item.revenue ?? 0,
    cost: item.cost ?? 0,
    profit: item.profit ?? 0,
  }));

  // 转换渠道数据格式 - 添加防护性检查
  // 计算总消耗用于百分比
  const channelData = channelDistribution ?? [];
  const totalChannelSpend = channelData.reduce((sum, item) => sum + (item.total_spend ?? 0), 0);
  const platformSpend = channelData.map(item => ({
    platform: item.channel_name ?? item.channel ?? '未知渠道',
    spend: item.total_spend ?? 0,
    percentage: totalChannelSpend > 0 ? ((item.total_spend ?? 0) / totalChannelSpend) * 100 : 0,
    trend: 'stable' as 'up' | 'down' | 'stable',
  }));

  // 从预警生成待办
  const alertsList = fundAlerts?.alerts ?? [];
  const todos = alertsList.map((alert, index) => ({
    id: index,
    type: alert.alert_type === 'negative_balance' ? 'alert' as const :
          alert.alert_type === 'overdue_receivable' ? 'settlement' as const : 'reconciliation' as const,
    title: alert.title,
    amount: alert.value,
    priority: (alert.severity === 'critical' ? 'high' : alert.severity) as 'high' | 'medium' | 'low',
    created_at: '',
  }));

  // 低余额账户 (从预警数据)
  const lowBalanceAccounts = alertsList
    .filter(a => a.alert_type === 'negative_balance')
    .map((alert, index) => ({
      id: index,
      name: alert.title,
      platform: alert.related_type || '未知',
      balance: alert.value ?? 0,
      status: alert.severity === 'critical' ? 'critical' as const : 'low' as const,
    }));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-100">
            <DollarSign className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">财务中心</h1>
            <p className="text-sm text-gray-500">财务概览、账户余额和资金管理</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          <Link href="/topups">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              申请充值
            </Button>
          </Link>
        </div>
      </div>

      {/* Overview Cards - v3.0 优化版 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
          <CardContent className="pt-6">
            {isLoadingOverview ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">累计充值</p>
                  <p className="text-3xl font-bold text-gray-900 tabular-nums">{formatMoney(overview.total_topup)}</p>
                  <div className="flex items-center text-green-600 text-sm">
                    <TrendingUp className="h-4 w-4" />
                    <span className="ml-1">总充值</span>
                  </div>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
          <CardContent className="pt-6">
            {isLoadingOverview ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">累计消耗</p>
                  <p className="text-3xl font-bold text-gray-900 tabular-nums">{formatMoney(overview.total_spend)}</p>
                  <div className="flex items-center text-red-600 text-sm">
                    <TrendingDown className="h-4 w-4" />
                    <span className="ml-1">总消耗</span>
                  </div>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-50">
                  <TrendingDown className="h-5 w-5 text-red-600" />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
          <CardContent className="pt-6">
            {isLoadingOverview ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">当前余额</p>
                  <p className="text-3xl font-bold text-green-600 tabular-nums">{formatMoney(overview.current_balance)}</p>
                  <div className="flex items-center text-gray-500 text-sm">
                    <span>占用率 {(overview.occupy_rate ?? 0).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                  <Wallet className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
          <CardContent className="pt-6">
            {isLoadingOverview ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">应收款</p>
                  <p className="text-3xl font-bold text-amber-600 tabular-nums">{formatMoney(overview.total_receivable)}</p>
                  <div className="flex items-center text-amber-600 text-sm">
                    <Clock className="h-4 w-4 mr-1" />
                    <span>待收 {overview.pending_count} 笔</span>
                  </div>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50">
                  <CreditCard className="h-5 w-5 text-amber-600" />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* 收支趋势图 */}
        <div className="col-span-12 lg:col-span-8">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    收支趋势
                  </CardTitle>
                  <CardDescription>最近7天收入与成本对比</CardDescription>
                </div>
                <Link href="/finance/profit">
                  <Button variant="ghost" size="sm">
                    详细分析 <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingTrend ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : trends.length === 0 ? (
                <div className="flex items-center justify-center py-12 text-gray-500">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p className="text-sm">暂无趋势数据</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {trends.map((day, index) => {
                    const maxValue = Math.max(...trends.map(t => Math.max(t.revenue, t.cost))) || 1;
                    return (
                      <div key={day.date} className="flex items-center gap-4">
                        <span className="w-12 text-sm text-gray-500">{day.date}</span>
                        <div className="flex-1 flex items-center gap-2">
                          <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden relative">
                            <div
                              className="absolute left-0 top-0 h-full bg-green-500 rounded-full"
                              style={{ width: `${(day.revenue / maxValue) * 100}%` }}
                            />
                            <div
                              className="absolute left-0 top-0 h-full bg-red-400 rounded-full opacity-60"
                              style={{ width: `${(day.cost / maxValue) * 100}%` }}
                            />
                          </div>
                          <div className="w-24 text-right">
                            <span className="text-sm font-medium text-green-600">
                              +{formatMoney(day.profit)}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  <div className="flex items-center justify-center gap-6 pt-2 border-t">
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
        </div>

        {/* 平台消耗占比 */}
        <div className="col-span-12 lg:col-span-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                平台消耗占比
              </CardTitle>
              <CardDescription>本月各平台广告消耗</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingChannels ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : platformSpend.length === 0 ? (
                <div className="flex items-center justify-center py-12 text-gray-500">
                  <div className="text-center">
                    <PieChart className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p className="text-sm">暂无平台数据</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {platformSpend.map((platform) => (
                    <div key={platform.platform}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{platform.platform}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">{formatMoney(platform.spend)}</span>
                          {platform.trend === 'up' && <ArrowUpRight className="h-4 w-4 text-green-500" />}
                          {platform.trend === 'down' && <ArrowDownRight className="h-4 w-4 text-red-500" />}
                        </div>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${platform.percentage}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{(platform.percentage ?? 0).toFixed(1)}%</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 财务待办 */}
        <div className="col-span-12 lg:col-span-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    财务待办
                  </CardTitle>
                  <CardDescription>需要处理的财务事项</CardDescription>
                </div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  {todos.filter(t => t.priority === 'high').length} 个紧急
                </span>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingAlerts ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : todos.length === 0 ? (
                <div className="flex items-center justify-center py-12 text-gray-500">
                  <div className="text-center">
                    <CheckCircle className="h-12 w-12 mx-auto text-green-300 mb-3" />
                    <p className="text-sm">暂无待办事项</p>
                    <p className="text-xs text-gray-400 mt-1">所有财务事项已处理完毕</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {todos.map((todo) => {
                    const config = todoConfig[todo.type] || todoConfig.alert;
                    const Icon = config.icon;
                    return (
                      <div key={todo.id} className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${config.bg}`}>
                          <Icon className={`h-5 w-5 ${config.color}`} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-900">{todo.title}</p>
                            <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${priorityColors[todo.priority]}`}>
                              {todo.priority === 'high' ? '紧急' : todo.priority === 'medium' ? '一般' : '低'}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            {todo.amount && (
                              <span className="text-sm text-gray-600">{formatMoney(todo.amount)}</span>
                            )}
                            <span className="text-xs text-gray-400">{todo.created_at}</span>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm">
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 低余额预警 */}
        <div className="col-span-12 lg:col-span-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-orange-500" />
                    余额预警
                  </CardTitle>
                  <CardDescription>余额不足的广告账户</CardDescription>
                </div>
                <Link href="/ad-accounts">
                  <Button variant="ghost" size="sm">
                    查看全部 <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingAlerts ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : lowBalanceAccounts.length === 0 ? (
                <div className="flex items-center justify-center py-12 text-gray-500">
                  <div className="text-center">
                    <CheckCircle className="h-12 w-12 mx-auto text-green-300 mb-3" />
                    <p className="text-sm">账户余额正常</p>
                    <p className="text-xs text-gray-400 mt-1">所有账户余额充足</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {lowBalanceAccounts.map((account) => (
                    <div key={account.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${account.status === 'critical' ? 'bg-red-500' : 'bg-yellow-500'}`} />
                        <div>
                          <p className="font-medium text-gray-900">{account.name}</p>
                          <p className="text-xs text-gray-500">{account.platform}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-bold ${account.status === 'critical' ? 'text-red-600' : 'text-yellow-600'}`}>
                          ¥{(account.balance ?? 0).toLocaleString()}
                        </p>
                        <Link href="/topups">
                          <Button variant="link" size="sm" className="h-auto p-0 text-xs">
                            立即充值
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 最近交易 */}
        <div className="col-span-12">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    最近交易
                  </CardTitle>
                  <CardDescription>最新的充值、消耗和结算记录</CardDescription>
                </div>
                <Link href="/reconciliation">
                  <Button variant="ghost" size="sm">
                    查看全部 <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center py-12 text-gray-500">
                <div className="text-center">
                  <FileText className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                  <p className="text-sm">交易记录功能开发中</p>
                  <p className="text-xs text-gray-400 mt-1">请前往充值管理或对账管理查看详细记录</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>快捷操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <Link href="/finance/fund">
              <Button variant="outline" className="w-full h-auto py-4 flex flex-col items-center gap-2">
                <Wallet className="h-6 w-6 text-green-600" />
                <span>资金总览</span>
              </Button>
            </Link>
            <Link href="/finance/profit">
              <Button variant="outline" className="w-full h-auto py-4 flex flex-col items-center gap-2">
                <PieChart className="h-6 w-6 text-orange-600" />
                <span>项目盈亏</span>
              </Button>
            </Link>
            <Link href="/topups">
              <Button variant="outline" className="w-full h-auto py-4 flex flex-col items-center gap-2">
                <CreditCard className="h-6 w-6 text-blue-600" />
                <span>充值管理</span>
              </Button>
            </Link>
            <Link href="/settlements">
              <Button variant="outline" className="w-full h-auto py-4 flex flex-col items-center gap-2">
                <FileText className="h-6 w-6 text-purple-600" />
                <span>结算管理</span>
              </Button>
            </Link>
            <Link href="/reconciliation">
              <Button variant="outline" className="w-full h-auto py-4 flex flex-col items-center gap-2">
                <CheckCircle className="h-6 w-6 text-green-600" />
                <span>对账管理</span>
              </Button>
            </Link>
            <Link href="/ad-accounts">
              <Button variant="outline" className="w-full h-auto py-4 flex flex-col items-center gap-2">
                <BarChart3 className="h-6 w-6 text-indigo-600" />
                <span>账户管理</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default FinancePage;
