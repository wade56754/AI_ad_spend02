/**
 * GlobalDateFilter Component
 *
 * 全局日期筛选组件 - 统一控制所有图表的时间范围
 * 支持：今天、近7天、近30天、自定义日期
 *
 * Based on UI_DESIGN_SYSTEM.md v2.0
 */

'use client';

import React from 'react';
import { Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type DateRangePreset = 'today' | '7d' | '30d' | 'custom';

interface DateRange {
  from: Date;
  to: Date;
}

interface GlobalDateFilterProps {
  value: DateRangePreset;
  onChange: (preset: DateRangePreset, range?: DateRange) => void;
  className?: string;
}

const PRESET_OPTIONS: Array<{ value: DateRangePreset; label: string }> = [
  { value: 'today', label: '今天' },
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
  { value: 'custom', label: '自定义' },
];

export function GlobalDateFilter({
  value,
  onChange,
  className,
}: GlobalDateFilterProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Calendar className="h-4 w-4 text-muted-foreground" />
      <div className="flex gap-1">
        {PRESET_OPTIONS.map((option) => (
          <Button
            key={option.value}
            variant={value === option.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => onChange(option.value)}
            className={cn(
              'px-3 py-1.5 h-8 text-xs font-medium transition-all',
              value === option.value && 'shadow-sm'
            )}
          >
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

/**
 * 根据预设值计算日期范围
 */
export function getDateRangeFromPreset(preset: DateRangePreset): DateRange {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const to = new Date(today);
  to.setHours(23, 59, 59, 999);

  let from = new Date(today);

  switch (preset) {
    case 'today':
      from = new Date(today);
      break;
    case '7d':
      from.setDate(today.getDate() - 6);
      break;
    case '30d':
      from.setDate(today.getDate() - 29);
      break;
    case 'custom':
      // 自定义日期范围，默认返回近30天
      from.setDate(today.getDate() - 29);
      break;
  }

  from.setHours(0, 0, 0, 0);

  return { from, to };
}

export default GlobalDateFilter;
