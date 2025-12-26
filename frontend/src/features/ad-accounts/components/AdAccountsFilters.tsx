/**
 * AdAccountsFilters Component
 *
 * 智能筛选栏 - 高频筛选条件前置
 * 从 AdAccountsPageV2.tsx 提取
 */

'use client';

import React, { useMemo } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { getStatusConfig, type AdAccountV2Display } from '../utils/adAccountsHelpers';

export interface AdAccountsFiltersProps {
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
  accounts: AdAccountV2Display[];
  className?: string;
}

export function AdAccountsFilters({
  filters,
  onFilterChange,
  accounts,
  className,
}: AdAccountsFiltersProps) {
  // 提取唯一值用于筛选
  const uniqueValues = useMemo(() => ({
    buyers: [...new Set(accounts.map(a => a.buyer))],
    suppliers: [...new Set(accounts.map(a => a.supplier))],
    accountTypes: [...new Set(accounts.map(a => a.accountType))],
    regions: [...new Set(accounts.map(a => a.region))],
  }), [accounts]);

  const handleClearFilters = () => {
    Object.keys(filters).forEach(key => onFilterChange(key, ''));
  };

  const hasActiveFilters = Object.values(filters).some(v => v);

  return (
    <div className={cn('flex items-center gap-3 flex-wrap', className)} data-testid="ad-accounts-filters">
      {/* 搜索框 - 支持模糊搜索 */}
      <div className="relative flex-1 min-w-[240px] max-w-[320px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          placeholder="搜索账户名称、ID、投手..."
          className="pl-9 h-9 bg-white"
          value={filters.search || ''}
          onChange={(e) => onFilterChange('search', e.target.value)}
        />
      </div>

      {/* 快捷状态筛选 - Tab 式切换 */}
      <div className="flex items-center bg-gray-100 rounded-lg p-1">
        {['all', 'active', 'testing', 'suspended', 'dead'].map((status) => (
          <button
            key={status}
            onClick={() => onFilterChange('status', status === 'all' ? '' : status)}
            className={cn(
              'px-3 py-1.5 text-xs font-medium rounded-md transition-all',
              (filters.status || '') === (status === 'all' ? '' : status)
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            )}
          >
            {status === 'all' ? '全部' : getStatusConfig(status).label}
          </button>
        ))}
      </div>

      {/* 投手筛选 */}
      <Select
        value={filters.buyer || '__all__'}
        onValueChange={(v) => onFilterChange('buyer', v === '__all__' ? '' : v)}
      >
        <SelectTrigger className="w-[120px] h-9 bg-white">
          <SelectValue placeholder="投手" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部投手</SelectItem>
          {uniqueValues.buyers.map(buyer => (
            <SelectItem key={buyer} value={buyer}>{buyer}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 代理商筛选 */}
      <Select
        value={filters.supplier || '__all__'}
        onValueChange={(v) => onFilterChange('supplier', v === '__all__' ? '' : v)}
      >
        <SelectTrigger className="w-[160px] h-9 bg-white">
          <SelectValue placeholder="代理商" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部代理商</SelectItem>
          {uniqueValues.suppliers.map(supplier => (
            <SelectItem key={supplier} value={supplier}>{supplier}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 平台筛选 */}
      <Select
        value={filters.platform || '__all__'}
        onValueChange={(v) => onFilterChange('platform', v === '__all__' ? '' : v)}
      >
        <SelectTrigger className="w-[100px] h-9 bg-white">
          <SelectValue placeholder="平台" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部</SelectItem>
          <SelectItem value="FB">Facebook</SelectItem>
          <SelectItem value="TK">TikTok</SelectItem>
        </SelectContent>
      </Select>

      {/* 更多筛选 */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-9">
            <SlidersHorizontal className="w-4 h-4 mr-1" />
            更多
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-[200px]">
          <DropdownMenuLabel>账户类型</DropdownMenuLabel>
          {uniqueValues.accountTypes.map(type => (
            <DropdownMenuCheckboxItem
              key={type}
              checked={filters.accountType === type}
              onCheckedChange={(checked) => onFilterChange('accountType', checked ? type : '')}
            >
              {type}
            </DropdownMenuCheckboxItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuLabel>地区</DropdownMenuLabel>
          {uniqueValues.regions.map(region => (
            <DropdownMenuCheckboxItem
              key={region}
              checked={filters.region === region}
              onCheckedChange={(checked) => onFilterChange('region', checked ? region : '')}
            >
              {region}
            </DropdownMenuCheckboxItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 清除筛选 */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          className="h-9 text-gray-500"
          onClick={handleClearFilters}
        >
          清除筛选
        </Button>
      )}
    </div>
  );
}

export default AdAccountsFilters;
