/**
 * FinanceTrendChart Component
 *
 * 收支趋势图 + 平台消耗占比 - 从 FinancePage.tsx 提取
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart3,
  PieChart,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { formatMoney, type TrendDataPoint, type PlatformSpend } from '../utils/financeHelpers';

interface FinanceTrendChartProps {
  trendData: TrendDataPoint[];
  platformSpend: PlatformSpend[];
  className?: string;
}

export function FinanceTrendChart({ trendData, platformSpend, className }: FinanceTrendChartProps) {
  return (
    <div className={`grid grid-cols-12 gap-6 ${className || ''}`} data-testid="finance-trend-chart">
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
            <div className="space-y-4">
              {trendData.map((day) => (
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
                  <p className="text-xs text-gray-500 mt-1">{platform.percentage}%</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default FinanceTrendChart;
