'use client';

/**
 * Finance Overview Page Component
 *
 * Route: /finance
 * Purpose: Financial dashboard with overview, trends, and quick actions
 * SoT 对齐: LEDGER_SOT.md v1.1, BUSINESS_RULES.md v3.2
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
  Plus
} from 'lucide-react';

// Mock data - 财务概览
const mockOverview = {
  total_revenue: 2580000,
  total_cost: 1890000,
  total_profit: 690000,
  profit_margin: 26.7,
  pending_settlements: 156000,
  pending_topups: 85000,
};

// Mock data - 趋势数据 (最近7天)
const mockTrends = [
  { date: '12-15', revenue: 320000, cost: 245000, profit: 75000 },
  { date: '12-16', revenue: 380000, cost: 278000, profit: 102000 },
  { date: '12-17', revenue: 350000, cost: 260000, profit: 90000 },
  { date: '12-18', revenue: 420000, cost: 310000, profit: 110000 },
  { date: '12-19', revenue: 390000, cost: 285000, profit: 105000 },
  { date: '12-20', revenue: 360000, cost: 268000, profit: 92000 },
  { date: '12-21', revenue: 360000, cost: 244000, profit: 116000 },
];

// Mock data - 低余额账户
const mockLowBalanceAccounts = [
  { id: 1, name: '巨量引擎-主账户', platform: '巨量引擎', balance: 5200, status: 'critical' as const },
  { id: 2, name: '腾讯广告-品牌号', platform: '腾讯广告', balance: 12800, status: 'low' as const },
  { id: 3, name: '快手磁力-效果号', platform: '快手', balance: 18500, status: 'low' as const },
];

// Mock data - 待办事项
const mockTodos = [
  { id: 1, type: 'topup' as const, title: '充值申请待审批', amount: 50000, priority: 'high' as const, created_at: '2024-12-21 09:30' },
  { id: 2, type: 'settlement' as const, title: '供应商结算待处理', amount: 86000, priority: 'high' as const, created_at: '2024-12-21 08:15' },
  { id: 3, type: 'reconciliation' as const, title: '日报对账待确认', amount: 125000, priority: 'medium' as const, created_at: '2024-12-20 17:00' },
  { id: 4, type: 'alert' as const, title: '账户余额预警', priority: 'high' as const, created_at: '2024-12-21 10:00' },
];

// Mock data - 最近交易
const mockTransactions = [
  { id: 1, type: 'topup' as const, account_name: '巨量引擎-主账户', amount: 100000, status: '已完成', created_at: '2024-12-21 10:30' },
  { id: 2, type: 'consume' as const, account_name: '腾讯广告-品牌号', amount: -28500, status: '已扣费', created_at: '2024-12-21 09:45' },
  { id: 3, type: 'topup' as const, account_name: '快手磁力-效果号', amount: 50000, status: '审批中', created_at: '2024-12-21 09:00' },
  { id: 4, type: 'settlement' as const, account_name: '供应商A', amount: -45000, status: '已结算', created_at: '2024-12-20 18:00' },
  { id: 5, type: 'consume' as const, account_name: '巨量引擎-主账户', amount: -32100, status: '已扣费', created_at: '2024-12-20 16:30' },
];

// Mock data - 平台消耗占比
const mockPlatformSpend = [
  { platform: '巨量引擎', spend: 890000, percentage: 47.1, trend: 'up' as const },
  { platform: '腾讯广告', spend: 560000, percentage: 29.6, trend: 'stable' as const },
  { platform: '快手磁力', spend: 320000, percentage: 16.9, trend: 'up' as const },
  { platform: '其他', spend: 120000, percentage: 6.4, trend: 'down' as const },
];

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
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

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
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">本月收入</p>
                <p className="text-3xl font-bold text-gray-900 tabular-nums">{formatMoney(mockOverview.total_revenue)}</p>
                <div className="flex items-center text-green-600 text-sm">
                  <ArrowUpRight className="h-4 w-4" />
                  <span>+12.5% 较上月</span>
                </div>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50">
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">本月成本</p>
                <p className="text-3xl font-bold text-gray-900 tabular-nums">{formatMoney(mockOverview.total_cost)}</p>
                <div className="flex items-center text-red-600 text-sm">
                  <ArrowUpRight className="h-4 w-4" />
                  <span>+8.2% 较上月</span>
                </div>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-50">
                <TrendingDown className="h-5 w-5 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">本月利润</p>
                <p className="text-3xl font-bold text-green-600 tabular-nums">{formatMoney(mockOverview.total_profit)}</p>
                <div className="flex items-center text-gray-500 text-sm">
                  <span>利润率 {mockOverview.profit_margin}%</span>
                </div>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                <PieChart className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">待结算金额</p>
                <p className="text-3xl font-bold text-amber-600 tabular-nums">{formatMoney(mockOverview.pending_settlements)}</p>
                <div className="flex items-center text-amber-600 text-sm">
                  <Clock className="h-4 w-4 mr-1" />
                  <span>3 笔待处理</span>
                </div>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50">
                <Wallet className="h-5 w-5 text-amber-600" />
              </div>
            </div>
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
              {/* Simple trend visualization */}
              <div className="space-y-4">
                {mockTrends.map((day, index) => (
                  <div key={day.date} className="flex items-center gap-4">
                    <span className="w-12 text-sm text-gray-500">{day.date}</span>
                    <div className="flex-1 flex items-center gap-2">
                      <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden relative">
                        <div
                          className="absolute left-0 top-0 h-full bg-green-500 rounded-full"
                          style={{ width: `${(day.revenue / 450000) * 100}%` }}
                        />
                        <div
                          className="absolute left-0 top-0 h-full bg-red-400 rounded-full opacity-60"
                          style={{ width: `${(day.cost / 450000) * 100}%` }}
                        />
                      </div>
                      <div className="w-24 text-right">
                        <span className="text-sm font-medium text-green-600">
                          +{formatMoney(day.profit)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
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
              <div className="space-y-4">
                {mockPlatformSpend.map((platform) => (
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
                    <p className="text-xs text-gray-500 mt-1">{platform.percentage}%</p>
                  </div>
                ))}
              </div>
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
                  {mockTodos.filter(t => t.priority === 'high').length} 个紧急
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockTodos.map((todo) => {
                  const config = todoConfig[todo.type];
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
              <div className="space-y-3">
                {mockLowBalanceAccounts.map((account) => (
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
                        ¥{account.balance.toLocaleString()}
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
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium text-gray-600">时间</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-600">类型</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-600">账户/对象</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">金额</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-600">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockTransactions.map((tx) => (
                      <tr key={tx.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {tx.created_at}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                            tx.type === 'topup' ? 'bg-green-100 text-green-800' :
                            tx.type === 'consume' ? 'bg-blue-100 text-blue-800' :
                            tx.type === 'settlement' ? 'bg-purple-100 text-purple-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {tx.type === 'topup' ? '充值' :
                             tx.type === 'consume' ? '消耗' :
                             tx.type === 'settlement' ? '结算' : '退款'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm font-medium text-gray-900">
                          {tx.account_name}
                        </td>
                        <td className={`py-3 px-4 text-sm font-bold text-right ${
                          tx.amount >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {tx.amount >= 0 ? '+' : ''}{formatMoney(tx.amount)}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {tx.status}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
            <Link href="/finance/profit">
              <Button variant="outline" className="w-full h-auto py-4 flex flex-col items-center gap-2">
                <PieChart className="h-6 w-6 text-orange-600" />
                <span>利润分析</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default FinancePage;
