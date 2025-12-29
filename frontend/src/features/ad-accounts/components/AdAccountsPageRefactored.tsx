/**
 * Ad Accounts Management Page (Refactored)
 *
 * 从原 895 行重构为 ~150 行
 * 子组件已提取到独立文件
 *
 * SoT: docs/10.module-specs/C1-project-mgmt.md (账户管理部分)
 */

'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { AdAccountsStats } from './AdAccountsStats';
import { AdAccountsFilters } from './AdAccountsFilters';
import { AdAccountsActions, type ColumnVisibility } from './AdAccountsActions';
import { AdAccountsTableV2 } from './AdAccountsTableV2';
import type { AdAccountV2Display } from '../utils/adAccountsHelpers';

// ============ Mock Data (TODO: 替换为 API 调用) ============
const mockAccounts: AdAccountV2Display[] = [
  {
    id: 1,
    name: 'SONZDD-ADA+7-GX-324',
    platformId: '1138647123633445',
    accountType: '越南盾主题户',
    platform: 'FB',
    supplier: '海总&志诚三不限',
    buyer: 'YK',
    region: '印度',
    status: 'active',
    todaySpend: 245.32,
    yesterdaySpend: 198.45,
    monthSpend: 4521.80,
    feeRate: 0.10,
    lastUpdated: '2025-12-22 14:30',
    trend: 23.6,
  },
  {
    id: 2,
    name: 'Tencent IS Pte.Ltd +8 -089',
    platformId: '270468399386879',
    accountType: '美金户',
    platform: 'FB',
    supplier: 'B哥-fb三不限10➕1',
    buyer: 'LM',
    region: '印度',
    status: 'active',
    todaySpend: 419.48,
    yesterdaySpend: 803.74,
    monthSpend: 3009.58,
    feeRate: 0.11,
    lastUpdated: '2025-12-22 14:25',
    trend: -47.8,
  },
  {
    id: 3,
    name: 'PeakTime-489',
    platformId: '2456962661335328',
    accountType: '美金户',
    platform: 'FB',
    supplier: '凤凰&洛阳',
    buyer: 'YJ',
    region: '新加坡',
    status: 'testing',
    todaySpend: 15.95,
    yesterdaySpend: 0,
    monthSpend: 217.89,
    feeRate: 0.11,
    lastUpdated: '2025-12-22 13:45',
    trend: 100,
  },
  {
    id: 4,
    name: 'SHARK 003 MAX',
    platformId: '1258285486025414',
    accountType: '绑卡户',
    platform: 'FB',
    supplier: '印度户印尼企业户',
    buyer: 'LD',
    region: '印度',
    status: 'suspended',
    todaySpend: 0,
    yesterdaySpend: 2.14,
    monthSpend: 506.08,
    feeRate: 0.07,
    lastUpdated: '2025-12-22 09:00',
    trend: -100,
  },
  {
    id: 5,
    name: 'TK-Global-HK-001',
    platformId: '7892345678901234',
    accountType: 'TK海外主体全球户',
    platform: 'TK',
    supplier: '官方授权户',
    buyer: 'HY',
    region: '加拿大',
    status: 'active',
    todaySpend: 89.50,
    yesterdaySpend: 76.30,
    monthSpend: 1285.82,
    feeRate: 0.05,
    lastUpdated: '2025-12-22 14:28',
    trend: 17.3,
  },
];

export function AdAccountsPageRefactored() {
  // ============ State ============
  const [accounts] = useState<AdAccountV2Display[]>(mockAccounts);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [columnVisibility, setColumnVisibility] = useState<ColumnVisibility>({
    accountName: true,
    buyer: true,
    supplier: true,
    todaySpend: true,
    monthSpend: true,
    feeRate: false,
    region: false,
  });

  // ============ Computed ============
  const filteredAccounts = useMemo(() => {
    return accounts.filter(account => {
      if (filters.search) {
        const search = filters.search.toLowerCase();
        if (
          !account.name.toLowerCase().includes(search) &&
          !account.platformId.includes(search) &&
          !account.buyer.toLowerCase().includes(search)
        ) {
          return false;
        }
      }
      if (filters.status && account.status !== filters.status) return false;
      if (filters.buyer && account.buyer !== filters.buyer) return false;
      if (filters.supplier && account.supplier !== filters.supplier) return false;
      if (filters.platform && account.platform !== filters.platform) return false;
      if (filters.accountType && account.accountType !== filters.accountType) return false;
      if (filters.region && account.region !== filters.region) return false;
      return true;
    });
  }, [accounts, filters]);

  // ============ Handlers ============
  const handleFilterChange = useCallback((key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleSelectChange = useCallback((id: number, checked: boolean) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      checked ? next.add(id) : next.delete(id);
      return next;
    });
  }, []);

  const handleSelectAll = useCallback((checked: boolean) => {
    setSelectedIds(checked ? new Set(filteredAccounts.map(a => a.id)) : new Set());
  }, [filteredAccounts]);

  const handleColumnVisibilityChange = useCallback((key: keyof ColumnVisibility, visible: boolean) => {
    setColumnVisibility(prev => ({ ...prev, [key]: visible }));
  }, []);

  const handleRefresh = useCallback(() => console.log('Refreshing...'), []);
  const handleExport = useCallback(() => console.log('Exporting...'), []);
  const handleImport = useCallback(() => console.log('Importing...'), []);

  // ============ Render ============
  return (
    <div className="space-y-4">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">广告账号管理</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            管理所有广告投放账户，监控消耗数据
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Clock className="w-3.5 h-3.5" />
          最后更新：2025-12-22 14:30
        </div>
      </div>

      {/* 统计卡片 */}
      <AdAccountsStats accounts={accounts} />

      {/* 主内容区 */}
      <Card>
        <CardContent className="p-4 space-y-4">
          {/* 筛选栏 */}
          <AdAccountsFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            accounts={accounts}
          />

          {/* 操作栏 */}
          <AdAccountsActions
            selectedCount={selectedIds.size}
            onRefresh={handleRefresh}
            onExport={handleExport}
            onImport={handleImport}
            columnVisibility={columnVisibility}
            onColumnVisibilityChange={handleColumnVisibilityChange}
          />

          {/* 账户表格 */}
          <AdAccountsTableV2
            accounts={filteredAccounts}
            selectedIds={selectedIds}
            onSelectChange={handleSelectChange}
            onSelectAll={handleSelectAll}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export default AdAccountsPageRefactored;
