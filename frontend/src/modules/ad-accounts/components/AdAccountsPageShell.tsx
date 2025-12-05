/**
 * AdAccountsPageShell - 广告账户页面主容器
 *
 * 布局结构：
 * - Header: 标题 + 平台筛选 + 搜索
 * - KPI 区: 账户数量、余额、消耗、风控
 * - 主内容: 账户列表表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Users, Plus, Search, RefreshCw, AlertCircle } from 'lucide-react';
import { PageShell } from '@/modules/shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AdAccountsKpiRow } from './AdAccountsKpiRow';
import { AdAccountsDataTable } from './AdAccountsDataTable';
import { useAdAccounts } from '../hooks';
import type { AdAccountPlatform, AdAccount } from '../types';

export function AdAccountsPageShell() {
  const router = useRouter();
  const {
    filteredAccounts,
    summary,
    loading,
    error,
    isEmpty,
    filters,
    setFilters,
    refresh,
  } = useAdAccounts();

  const handleSearch = (value: string) => {
    setFilters({ ...filters, search: value });
  };

  const handlePlatformChange = (value: string) => {
    if (value === 'all') {
      const { platform, ...rest } = filters;
      setFilters(rest);
    } else {
      setFilters({ ...filters, platform: value as AdAccountPlatform });
    }
  };

  const handleRowClick = (account: AdAccount) => {
    // Navigate to detail page under dashboard route
    router.push(`/dashboard/ad-accounts/${account.id}`);
  };

  const handleAddAccount = () => {
    // TODO: Implement add account modal/page
    router.push('/dashboard/ad-accounts/new');
  };

  // Render error state
  if (error && !loading) {
    return (
      <PageShell
        title="渠道账户"
        description="管理广告渠道账户，包括账户余额、状态和关联项目"
        icon={Users}
      >
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="p-4 rounded-full bg-danger/10 mb-4">
            <AlertCircle className="w-8 h-8 text-danger" />
          </div>
          <h3 className="text-lg font-semibold text-text-strong mb-2">
            加载失败
          </h3>
          <p className="text-text-muted mb-4 max-w-md">
            {error.message || '无法加载广告账户数据，请稍后重试'}
          </p>
          <Button
            onClick={refresh}
            variant="outline"
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            重新加载
          </Button>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="渠道账户"
      description="管理广告渠道账户，包括账户余额、状态和关联项目"
      icon={Users}
      filters={
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input
              placeholder="搜索账户..."
              className="pl-9 w-[200px] bg-card-bg border-border-default text-text-body placeholder:text-text-muted"
              value={filters.search || ''}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>
          <Select
            onValueChange={handlePlatformChange}
            value={filters.platform || 'all'}
          >
            <SelectTrigger className="w-[120px] bg-card-bg border-border-default text-text-body">
              <SelectValue placeholder="平台" />
            </SelectTrigger>
            <SelectContent className="bg-card-bg border-border-default">
              <SelectItem value="all" className="text-text-body hover:bg-elevated">全部平台</SelectItem>
              <SelectItem value="meta" className="text-text-body hover:bg-elevated">Meta</SelectItem>
              <SelectItem value="google" className="text-text-body hover:bg-elevated">Google</SelectItem>
              <SelectItem value="tiktok" className="text-text-body hover:bg-elevated">TikTok</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="ghost"
            size="icon"
            onClick={refresh}
            disabled={loading}
            className="text-text-muted hover:text-text-body hover:bg-elevated"
            title="刷新数据"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </>
      }
      actions={
        <Button
          size="sm"
          onClick={handleAddAccount}
          className="gap-2 bg-accent hover:bg-accent-hover shadow-lg shadow-accent/20"
        >
          <Plus className="w-4 h-4" />
          添加账户
        </Button>
      }
      kpiSection={<AdAccountsKpiRow summary={summary} loading={loading} />}
    >
      <AdAccountsDataTable
        accounts={filteredAccounts}
        loading={loading}
        isEmpty={isEmpty}
        onRowClick={handleRowClick}
        onRefresh={refresh}
      />
    </PageShell>
  );
}

export default AdAccountsPageShell;
