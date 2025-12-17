/**
 * GlobalFilters Component
 *
 * 全局筛选控件：日期 + 渠道 + 账户
 * 替代原有的 GlobalDateFilter，增加渠道和账户维度
 *
 * Based on UI_DESIGN_SYSTEM.md v2.0
 */

'use client';

import React from 'react';
import { Calendar, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import {
  useFilters,
  type DateRangePreset,
  type Channel,
} from '../context/FilterContext';

interface GlobalFiltersProps {
  className?: string;
}

const DATE_PRESETS: { value: DateRangePreset; label: string }[] = [
  { value: 'today', label: '今日' },
  { value: '7d', label: '近 7 天' },
  { value: '30d', label: '近 30 天' },
  { value: 'custom', label: '自定义' },
];

const CHANNELS: { value: Channel; label: string }[] = [
  { value: 'all', label: '全部渠道' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'google', label: 'Google Ads' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'other', label: '其他' },
];

// TODO: 从 API 获取账户列表
const MOCK_ACCOUNTS = [
  { id: 'all', name: '全部账户' },
  { id: 'acc001', name: 'FB-品牌主账户' },
  { id: 'acc002', name: 'FB-ROI优化组' },
  { id: 'acc003', name: 'Google-搜索广告' },
  { id: 'acc004', name: 'TikTok-A类视频' },
];

export function GlobalFilters({ className }: GlobalFiltersProps) {
  const { filters, updateFilters } = useFilters();

  return (
    <div className={cn('flex items-center gap-3', className)}>
      {/* 日期筛选 */}
      <div className="flex items-center gap-2 border border-border rounded-lg px-3 py-2 bg-background">
        <Calendar className="h-4 w-4 text-muted-foreground" />
        <Select
          value={filters.datePreset}
          onValueChange={(value) => updateFilters({ datePreset: value as DateRangePreset })}
        >
          <SelectTrigger className="h-auto border-none bg-transparent p-0 focus:ring-0 focus:ring-offset-0">
            <SelectValue placeholder="选择日期范围" />
          </SelectTrigger>
          <SelectContent>
            {DATE_PRESETS.map((preset) => (
              <SelectItem key={preset.value} value={preset.value}>
                {preset.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* 渠道筛选 */}
      <div className="flex items-center gap-2 border border-border rounded-lg px-3 py-2 bg-background">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <Select
          value={filters.channel}
          onValueChange={(value) => updateFilters({ channel: value as Channel })}
        >
          <SelectTrigger className="h-auto border-none bg-transparent p-0 focus:ring-0 focus:ring-offset-0 min-w-[120px]">
            <SelectValue placeholder="选择渠道" />
          </SelectTrigger>
          <SelectContent>
            {CHANNELS.map((channel) => (
              <SelectItem key={channel.value} value={channel.value}>
                {channel.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* 账户筛选 */}
      <Select
        value={filters.accountId || 'all'}
        onValueChange={(value) =>
          updateFilters({ accountId: value === 'all' ? undefined : value })
        }
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="选择账户" />
        </SelectTrigger>
        <SelectContent>
          {MOCK_ACCOUNTS.map((account) => (
            <SelectItem key={account.id} value={account.id}>
              {account.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 重置按钮 */}
      {(filters.datePreset !== '7d' || filters.channel !== 'all' || filters.accountId) && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => updateFilters({ datePreset: '7d', channel: 'all', accountId: undefined })}
          className="text-muted-foreground hover:text-foreground"
        >
          重置
        </Button>
      )}
    </div>
  );
}
