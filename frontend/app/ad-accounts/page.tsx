'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import PageContainer from '@/components/layout/page-container';
import { AdAccountTable } from './components/AdAccountTable';
import { AdAccountFilters } from './components/AdAccountFilters';
import { AdAccountSummaryCards } from './components/AdAccountSummaryCards';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import type { AdAccount, AdAccountFilters as FilterState, AdAccountStats } from './types';

// Mock data - 实际应该从 API 获取
const mockAccounts: AdAccount[] = [
  {
    id: 1,
    account_name: '测试账户1',
    platform: 'tiktok',
    account_id: '123456',
    account_status: 'active',
    account_type: 'business',
    currency: 'CNY',
    timezone: 'Asia/Shanghai',
    spending_limit: 50000,
    current_spend: 5000,
    balance: 10000,
    creation_time: '2024-01-01T00:00:00Z',
    last_active: '2024-01-15T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
    created_by: 'system',
  },
];

// Mock stats - 实际应该从 API 获取
const mockStats: AdAccountStats = {
  total_accounts: 1,
  active_accounts: 1,
  paused_accounts: 0,
  banned_accounts: 0,
  pending_accounts: 0,
  total_spending_limit: 50000,
  total_current_spend: 5000,
  total_balance: 10000,
  average_performance_score: 85,
  high_risk_accounts: 0,
  accounts_needing_attention: 0,
  accounts_by_platform: {
    facebook: 0,
    tiktok: 1,
    google: 0,
    twitter: 0,
    instagram: 0,
    youtube: 0,
    linkedin: 0,
  },
  accounts_by_status: {
    active: 1,
    paused: 0,
    banned: 0,
    pending: 0,
    restricted: 0,
  },
  total_conversions: 0,
  average_roas: 0,
  last_24h_spend: 0,
  last_7d_spend: 0,
  last_30d_spend: 5000,
  utilization_rate: 10,
};

export default function AdAccountsPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<FilterState>({
    search_term: '',
    platform: 'all',
    status: 'all',
    type: 'all',
    assigned_user_id: 'all',
    project_id: 'all',
    client_id: 'all',
    risk_level: 'all',
    balance_range: {},
    spend_range: {},
    date_range: {},
    has_issues: null,
    auto_optimization: null,
    tags: [],
    sort_by: 'account_name',
    sort_order: 'asc',
  });
  const [accounts] = useState<AdAccount[]>(mockAccounts);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const handleCreateAccount = () => {
    // TODO: 实现创建账户逻辑
    router.push('/ad-accounts/new');
  };

  const handleRowClick = (account: AdAccount) => {
    router.push(`/ad-accounts/${account.id}`);
  };

  const handleViewDetail = (account: AdAccount) => {
    router.push(`/ad-accounts/${account.id}`);
  };

  const handleEdit = (account: AdAccount) => {
    router.push(`/ad-accounts/${account.id}/edit`);
  };

  return (
    <PageContainer>
      <div className="flex flex-col gap-6 w-full">
        {/* 页面标题 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">渠道账户</h1>
            <p className="text-muted-foreground">
              管理广告渠道账户，包括账户余额、状态和关联项目
            </p>
          </div>
          <Button onClick={handleCreateAccount}>
            <Plus className="mr-2 h-4 w-4" />
            新建账户
          </Button>
        </div>

        {/* 统计卡片 */}
        <AdAccountSummaryCards stats={mockStats} loading={false} />

        {/* 筛选器 */}
        <AdAccountFilters
          filters={filters}
          onFiltersChange={setFilters}
        />

        {/* 账户列表 */}
        <AdAccountTable
          data={accounts}
          loading={false}
          onRowClick={handleRowClick}
          onViewDetail={handleViewDetail}
          onEdit={handleEdit}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
        />
      </div>
    </PageContainer>
  );
}

