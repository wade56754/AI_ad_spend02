/**
 * AdSpendPage Component
 *
 * 广告消耗数据页面
 */

'use client';

import React, { useState } from 'react';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Calendar,
  Filter,
  Download,
  BarChart3,
  Users,
  MousePointer,
  Eye,
} from 'lucide-react';

// Mock data
const mockSpendData = [
  {
    id: 1,
    account_name: '账户A-抖音',
    project_name: '项目Alpha',
    channel_name: '抖音',
    report_date: '2024-12-08',
    spend: 15680.50,
    impressions: 125000,
    clicks: 3200,
    conversions: 156,
    ctr: 2.56,
    cpc: 4.90,
    cpa: 100.52,
  },
  {
    id: 2,
    account_name: '账户B-快手',
    project_name: '项目Beta',
    channel_name: '快手',
    report_date: '2024-12-08',
    spend: 12350.00,
    impressions: 98000,
    clicks: 2800,
    conversions: 134,
    ctr: 2.86,
    cpc: 4.41,
    cpa: 92.16,
  },
  {
    id: 3,
    account_name: '账户C-百度',
    project_name: '项目Gamma',
    channel_name: '百度',
    report_date: '2024-12-08',
    spend: 8920.00,
    impressions: 76000,
    clicks: 1900,
    conversions: 89,
    ctr: 2.50,
    cpc: 4.69,
    cpa: 100.22,
  },
];

const mockSummary = {
  total_spend: 125680.50,
  total_impressions: 1250000,
  total_clicks: 32000,
  total_conversions: 1560,
  avg_ctr: 2.56,
  avg_cpc: 3.93,
  avg_cpa: 80.56,
  spend_change: 8.5,
  conversions_change: 12.3,
};

interface StatCardProps {
  title: string;
  value: string;
  change?: number;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ title, value, change, icon, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${color}`}>{icon}</div>
        {change !== undefined && (
          <div
            className={`flex items-center text-sm ${
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
}

export function AdSpendPage() {
  const [dateRange, setDateRange] = useState({
    start_date: '',
    end_date: '',
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('zh-CN').format(value);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsRefreshing(false);
  };

  const handleExport = () => {
    alert('导出功能开发中...');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <DollarSign className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">广告消耗</h1>
                <p className="text-sm text-gray-500">查看和分析广告投放消耗数据</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                <Download className="h-4 w-4" />
                导出
              </button>
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                刷新
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <input
                type="date"
                value={dateRange.start_date}
                onChange={(e) =>
                  setDateRange((prev) => ({ ...prev, start_date: e.target.value }))
                }
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-gray-400">-</span>
              <input
                type="date"
                value={dateRange.end_date}
                onChange={(e) =>
                  setDateRange((prev) => ({ ...prev, end_date: e.target.value }))
                }
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
              <option value="">全部项目</option>
              <option value="1">项目Alpha</option>
              <option value="2">项目Beta</option>
            </select>
            <select className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
              <option value="">全部渠道</option>
              <option value="1">抖音</option>
              <option value="2">快手</option>
              <option value="3">百度</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="总消耗"
            value={formatCurrency(mockSummary.total_spend)}
            change={mockSummary.spend_change}
            icon={<DollarSign className="h-6 w-6 text-blue-600" />}
            color="bg-blue-50"
          />
          <StatCard
            title="总粉数"
            value={formatNumber(mockSummary.total_conversions)}
            change={mockSummary.conversions_change}
            icon={<Users className="h-6 w-6 text-green-600" />}
            color="bg-green-50"
          />
          <StatCard
            title="平均CPA"
            value={formatCurrency(mockSummary.avg_cpa)}
            icon={<BarChart3 className="h-6 w-6 text-purple-600" />}
            color="bg-purple-50"
          />
          <StatCard
            title="平均CTR"
            value={`${mockSummary.avg_ctr.toFixed(2)}%`}
            icon={<MousePointer className="h-6 w-6 text-orange-600" />}
            color="bg-orange-50"
          />
        </div>
      </div>

      {/* Data Table */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 pb-8">
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">消耗明细</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    账户
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    项目
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    渠道
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    日期
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    消耗
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    曝光
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    点击
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    粉数
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    CTR
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    CPA
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {mockSpendData.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.account_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {item.project_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
                        {item.channel_name}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {item.report_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      {formatCurrency(item.spend)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                      {formatNumber(item.impressions)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                      {formatNumber(item.clicks)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-green-600">
                      {item.conversions}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                      {item.ctr.toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatCurrency(item.cpa)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-6 py-4 border-t flex items-center justify-between">
            <div className="text-sm text-gray-500">
              显示 1-{mockSpendData.length} 共 {mockSpendData.length} 条
            </div>
            <div className="flex gap-2">
              <button
                disabled
                className="px-3 py-1 border rounded text-sm text-gray-400 cursor-not-allowed"
              >
                上一页
              </button>
              <button
                disabled
                className="px-3 py-1 border rounded text-sm text-gray-400 cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdSpendPage;
