/**
 * DashboardPage Component
 *
 * Main dashboard with metrics overview
 */

'use client';

import React from 'react';
import Link from 'next/link';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  FileText,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowRight,
  RefreshCw,
  BarChart3,
  Wallet,
  Target,
} from 'lucide-react';
import { useAuth } from '@/modules/auth';
import { QUICK_ACTIONS } from '../types';

// Stat Card Component
interface StatCardProps {
  title: string;
  value: string | number;
  change?: number | null;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red';
  href?: string;
}

function StatCard({ title, value, change, icon, color, href }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
    red: 'bg-red-50 text-red-600',
  };

  const content = (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        {change !== null && change !== undefined && (
          <div
            className={`flex items-center text-sm font-medium ${
              change >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {change >= 0 ? (
              <TrendingUp className="h-4 w-4 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 mr-1" />
            )}
            {Math.abs(change).toFixed(1)}%
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-sm text-gray-500">{title}</div>
    </div>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }

  return content;
}

// Pending Item Component
interface PendingItemProps {
  title: string;
  count: number;
  href: string;
  icon: React.ReactNode;
}

function PendingItem({ title, count, href, icon }: PendingItemProps) {
  return (
    <Link
      href={href}
      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
    >
      <div className="flex items-center gap-3">
        <div className="p-2 bg-white rounded-lg text-gray-600">{icon}</div>
        <span className="text-sm font-medium text-gray-700">{title}</span>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`px-2 py-1 rounded-full text-xs font-semibold ${
            count > 0 ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'
          }`}
        >
          {count}
        </span>
        <ArrowRight className="h-4 w-4 text-gray-400" />
      </div>
    </Link>
  );
}

export function DashboardPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  // Mock data - in real app, fetch from API
  // TODO: Replace with actual API call using React Query
  const stats = {
    today_spend: 125680.50,
    today_conversions: 3256,
    today_revenue: 162500.00,
    today_profit: 36819.50,
    spend_change: 12.5,
    conversions_change: 8.3,
    profit_change: 15.2,
    pending_topups: 3,
    pending_settlements: 2,
    pending_reconciliations: 5,
    pending_imports: 1,
    active_projects: 12,
    active_accounts: 45,
    total_balance: 856000.00,
  };

  // Show loading state while auth is initializing
  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // TODO: Replace with actual API refresh call
      // await refetchDashboardStats();
      // Simulate refresh
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      console.error('刷新数据失败:', error);
      // TODO: Show error toast notification
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                欢迎回来，{user?.full_name || user?.username || '用户'}
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                这是您的系统概览，查看今日数据和待处理事项
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              刷新
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Today's Stats */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">今日概览</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="今日消耗"
              value={formatCurrency(stats.today_spend)}
              change={stats.spend_change}
              icon={<DollarSign className="h-6 w-6" />}
              color="blue"
              href="/ad-spend"
            />
            <StatCard
              title="今日粉数"
              value={stats.today_conversions.toLocaleString()}
              change={stats.conversions_change}
              icon={<Users className="h-6 w-6" />}
              color="green"
              href="/daily-reports"
            />
            <StatCard
              title="今日收入"
              value={formatCurrency(stats.today_revenue)}
              icon={<BarChart3 className="h-6 w-6" />}
              color="purple"
              href="/finance/profit"
            />
            <StatCard
              title="今日利润"
              value={formatCurrency(stats.today_profit)}
              change={stats.profit_change}
              icon={<Target className="h-6 w-6" />}
              color="orange"
              href="/finance/profit"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Pending Items */}
          <div className="lg:col-span-2 space-y-8">
            {/* Pending Tasks */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">待处理事项</h3>
              <div className="space-y-3">
                <PendingItem
                  title="待审批充值"
                  count={stats.pending_topups}
                  href="/topups?status=pending"
                  icon={<CreditCard className="h-5 w-5" />}
                />
                <PendingItem
                  title="待结算项目"
                  count={stats.pending_settlements}
                  href="/settlements?status=pending"
                  icon={<Wallet className="h-5 w-5" />}
                />
                <PendingItem
                  title="待对账记录"
                  count={stats.pending_reconciliations}
                  href="/reconciliation?status=pending"
                  icon={<CheckCircle className="h-5 w-5" />}
                />
                <PendingItem
                  title="待处理导入"
                  count={stats.pending_imports}
                  href="/import-jobs?status=pending"
                  icon={<FileText className="h-5 w-5" />}
                />
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">快捷操作</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {QUICK_ACTIONS.map((action) => (
                  <Link
                    key={action.id}
                    href={action.href}
                    className="flex flex-col items-center gap-2 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div
                      className={`p-3 rounded-full ${
                        action.color === 'blue'
                          ? 'bg-blue-100 text-blue-600'
                          : action.color === 'green'
                          ? 'bg-green-100 text-green-600'
                          : action.color === 'purple'
                          ? 'bg-purple-100 text-purple-600'
                          : 'bg-orange-100 text-orange-600'
                      }`}
                    >
                      {action.icon === 'file-plus' && <FileText className="h-5 w-5" />}
                      {action.icon === 'plus-circle' && <CreditCard className="h-5 w-5" />}
                      {action.icon === 'upload' && <FileText className="h-5 w-5" />}
                      {action.icon === 'check-square' && <CheckCircle className="h-5 w-5" />}
                    </div>
                    <span className="text-sm font-medium text-gray-700">{action.label}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Summary */}
          <div className="space-y-6">
            {/* Account Summary */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">账户概览</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b">
                  <span className="text-sm text-gray-500">活跃项目</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.active_projects}
                  </span>
                </div>
                <div className="flex items-center justify-between py-3 border-b">
                  <span className="text-sm text-gray-500">广告账户</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.active_accounts}
                  </span>
                </div>
                <div className="flex items-center justify-between py-3">
                  <span className="text-sm text-gray-500">账户余额</span>
                  <span className="text-lg font-semibold text-green-600">
                    {formatCurrency(stats.total_balance)}
                  </span>
                </div>
              </div>
              <Link
                href="/ledger"
                className="mt-4 flex items-center justify-center gap-2 w-full py-2 text-sm text-blue-600 hover:text-blue-700"
              >
                查看账本明细
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">系统状态</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">API 服务正常</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">数据库连接正常</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">定时任务运行中</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
