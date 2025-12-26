/**
 * AdAccountsStats Component
 *
 * 顶部统计卡片 - 关键指标一眼可见
 * 从 AdAccountsPageV2.tsx 提取
 */

'use client';

import React, { useMemo } from 'react';
import { Users, Zap, DollarSign, BarChart3, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { formatCurrency, formatPercent } from '../utils/adAccountsHelpers';

export interface AdAccountStatsData {
  id: number;
  status: 'active' | 'testing' | 'suspended' | 'dead' | 'new';
  todaySpend: number;
  yesterdaySpend: number;
  monthSpend: number;
}

interface AdAccountsStatsProps {
  accounts: AdAccountStatsData[];
  className?: string;
}

export function AdAccountsStats({ accounts, className }: AdAccountsStatsProps) {
  const stats = useMemo(() => {
    const active = accounts.filter(a => a.status === 'active').length;
    const todayTotal = accounts.reduce((sum, a) => sum + a.todaySpend, 0);
    const yesterdayTotal = accounts.reduce((sum, a) => sum + a.yesterdaySpend, 0);
    const monthTotal = accounts.reduce((sum, a) => sum + a.monthSpend, 0);
    const trend = yesterdayTotal > 0 ? ((todayTotal - yesterdayTotal) / yesterdayTotal) * 100 : 0;
    const avgFeeRate = 0.092; // TODO: 计算实际平均费率

    return { active, total: accounts.length, todayTotal, monthTotal, trend, avgFeeRate };
  }, [accounts]);

  return (
    <div className={`grid grid-cols-4 gap-4 ${className || ''}`} data-testid="ad-accounts-stats">
      {/* 账户总数 */}
      <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-xs font-medium">账户总数</p>
              <p className="text-2xl font-bold mt-1">{stats.total}</p>
              <p className="text-blue-100 text-xs mt-1">
                <span className="text-white font-medium">{stats.active}</span> 个投放中
              </p>
            </div>
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 今日消耗 */}
      <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-xs font-medium">今日消耗</p>
              <p className="text-2xl font-bold mt-1">{formatCurrency(stats.todayTotal)}</p>
              <p className="text-green-100 text-xs mt-1 flex items-center gap-1">
                {stats.trend >= 0 ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                <span className={stats.trend >= 0 ? 'text-white' : 'text-green-200'}>
                  {formatPercent(stats.trend)}
                </span>
                vs 昨日
              </p>
            </div>
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 本月消耗 */}
      <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-xs font-medium">本月消耗</p>
              <p className="text-2xl font-bold mt-1">{formatCurrency(stats.monthTotal)}</p>
              <p className="text-purple-100 text-xs mt-1">
                日均 <span className="text-white font-medium">{formatCurrency(stats.monthTotal / 22)}</span>
              </p>
            </div>
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 平均费率 */}
      <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-0">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-xs font-medium">平均费率</p>
              <p className="text-2xl font-bold mt-1">{(stats.avgFeeRate * 100).toFixed(1)}%</p>
              <p className="text-orange-100 text-xs mt-1">
                手续费 <span className="text-white font-medium">{formatCurrency(stats.todayTotal * stats.avgFeeRate)}</span>
              </p>
            </div>
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default AdAccountsStats;
