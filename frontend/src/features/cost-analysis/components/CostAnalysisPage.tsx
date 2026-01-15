'use client';

/**
 * Cost Analysis Page Component
 *
 * Route: /cost-analysis
 * Purpose: Display cost breakdown and analysis
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  PieChart,
  BarChart3,
  Calendar,
  RefreshCw,
} from 'lucide-react';

// Mock data for demonstration
const mockSummary = {
  total_cost: 125680.5,
  media_cost: 98500.0,
  service_fee: 15680.5,
  other_cost: 11500.0,
};

const mockBreakdown = [
  { category: '媒体消耗', amount: 98500, percentage: 78.4, trend: 5.2 },
  { category: '服务费', amount: 15680.5, percentage: 12.5, trend: -2.1 },
  { category: '技术成本', amount: 6500, percentage: 5.2, trend: 0 },
  { category: '其他费用', amount: 5000, percentage: 3.9, trend: 1.5 },
];

export function CostAnalysisPage() {
  const [dateRange, setDateRange] = useState('month');
  const [isLoading, setIsLoading] = useState(false);

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1000);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100">
            <PieChart className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">成本分析</h1>
            <p className="text-sm text-gray-500">分析广告投放成本结构与趋势</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border bg-white p-1">
            {['week', 'month', 'quarter', 'year'].map((range) => (
              <Button
                key={range}
                onClick={() => setDateRange(range)}
                variant="ghost"
                size="sm"
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  dateRange === range ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {range === 'week' && '本周'}
                {range === 'month' && '本月'}
                {range === 'quarter' && '本季'}
                {range === 'year' && '本年'}
              </Button>
            ))}
          </div>
          <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">总成本</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(mockSummary.total_cost)}
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
                <DollarSign className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">媒体消耗</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(mockSummary.media_cost)}
                </p>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  占比 78.4%
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                <BarChart3 className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">服务费</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(mockSummary.service_fee)}
                </p>
                <p className="text-xs text-red-600 flex items-center mt-1">
                  <TrendingDown className="h-3 w-3 mr-1" />
                  占比 12.5%
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-orange-100">
                <DollarSign className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">其他成本</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(mockSummary.other_cost)}
                </p>
                <p className="text-xs text-gray-600 flex items-center mt-1">占比 9.1%</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
                <Calendar className="h-6 w-6 text-gray-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cost Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PieChart className="h-5 w-5" />
            成本构成明细
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-b">
                  <TableHead className="text-left py-3 px-4 font-medium text-gray-600">
                    类别
                  </TableHead>
                  <TableHead className="text-right py-3 px-4 font-medium text-gray-600">
                    金额
                  </TableHead>
                  <TableHead className="text-right py-3 px-4 font-medium text-gray-600">
                    占比
                  </TableHead>
                  <TableHead className="text-right py-3 px-4 font-medium text-gray-600">
                    环比变化
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockBreakdown.map((item, index) => (
                  <TableRow key={index} className="border-b hover:bg-gray-50">
                    <TableCell className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{
                            backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#6B7280'][index],
                          }}
                        />
                        {item.category}
                      </div>
                    </TableCell>
                    <TableCell className="text-right py-3 px-4 font-medium">
                      {formatCurrency(item.amount)}
                    </TableCell>
                    <TableCell className="text-right py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-600 rounded-full"
                            style={{ width: `${item.percentage}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600 w-12">{item.percentage}%</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right py-3 px-4">
                      <span
                        className={`flex items-center justify-end gap-1 ${
                          item.trend > 0
                            ? 'text-red-600'
                            : item.trend < 0
                              ? 'text-green-600'
                              : 'text-gray-600'
                        }`}
                      >
                        {item.trend > 0 ? (
                          <TrendingUp className="h-4 w-4" />
                        ) : item.trend < 0 ? (
                          <TrendingDown className="h-4 w-4" />
                        ) : null}
                        {item.trend > 0 ? '+' : ''}
                        {item.trend}%
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Placeholder for Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            成本趋势图
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
            <div className="text-center text-gray-500">
              <BarChart3 className="h-12 w-12 mx-auto mb-2 text-gray-400" />
              <p>成本趋势图表</p>
              <p className="text-sm">（集成图表库后显示）</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default CostAnalysisPage;
