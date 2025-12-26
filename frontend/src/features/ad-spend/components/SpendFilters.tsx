/**
 * SpendFilters Component
 *
 * SoT: docs/10.module-specs/C3-spend-detail.md §3.1
 * CodeBlock: CB-FE-003 (GlobalFilters)
 *
 * 功能: 消耗明细筛选器
 */

'use client';

import React from 'react';
import { Calendar } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AdSpendListParams } from '../types';

export interface SpendFiltersProps {
  filters: AdSpendListParams;
  onChange: (filters: Partial<AdSpendListParams>) => void;
  aggregateBy: 'none' | 'date' | 'project' | 'account';
  onAggregateChange: (value: 'none' | 'date' | 'project' | 'account') => void;
}

export function SpendFilters({
  filters,
  onChange,
  aggregateBy,
  onAggregateChange,
}: SpendFiltersProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <div className="space-y-1">
              <Label className="text-xs">开始日期</Label>
              <Input
                type="date"
                value={filters.start_date || ''}
                onChange={(e) => onChange({ start_date: e.target.value })}
                className="w-36"
              />
            </div>
            <span className="text-muted-foreground mt-6">-</span>
            <div className="space-y-1">
              <Label className="text-xs">结束日期</Label>
              <Input
                type="date"
                value={filters.end_date || ''}
                onChange={(e) => onChange({ end_date: e.target.value })}
                className="w-36"
              />
            </div>
          </div>

          <div className="space-y-1">
            <Label className="text-xs">项目</Label>
            <Select
              value={filters.project_id?.toString() || '__all__'}
              onValueChange={(v) => onChange({ project_id: v === '__all__' ? undefined : Number(v) })}
            >
              <SelectTrigger className="w-36">
                <SelectValue placeholder="全部项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部项目</SelectItem>
                <SelectItem value="1">项目Alpha</SelectItem>
                <SelectItem value="2">项目Beta</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label className="text-xs">渠道</Label>
            <Select
              value={filters.channel_id?.toString() || '__all__'}
              onValueChange={(v) => onChange({ channel_id: v === '__all__' ? undefined : Number(v) })}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="全部渠道" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部渠道</SelectItem>
                <SelectItem value="1">抖音</SelectItem>
                <SelectItem value="2">快手</SelectItem>
                <SelectItem value="3">百度</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label className="text-xs">聚合维度</Label>
            <Select value={aggregateBy} onValueChange={onAggregateChange}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="不聚合" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">不聚合</SelectItem>
                <SelectItem value="date">按日期</SelectItem>
                <SelectItem value="project">按项目</SelectItem>
                <SelectItem value="account">按账户</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default SpendFilters;
