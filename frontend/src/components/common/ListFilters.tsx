/**
 * ListFilters - 通用筛选器组件
 *
 * TASK-FE-COMMON-005: 通用列表页模板
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
 */

'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Badge } from '@/components/ui/badge';
import { CalendarIcon, X, Filter } from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import type { DateRange } from 'react-day-picker';

// === 类型定义 ===

export interface FilterOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectFilterProps {
  /** 筛选器标签 */
  label: string;
  /** 当前值 */
  value?: string;
  /** 选项列表 */
  options: FilterOption[];
  /** 值变化回调 */
  onChange: (value: string | undefined) => void;
  /** 占位符 */
  placeholder?: string;
  /** 是否允许清空 */
  clearable?: boolean;
  /** 自定义类名 */
  className?: string;
}

export interface DateFilterProps {
  /** 筛选器标签 */
  label: string;
  /** 当前值 */
  value?: Date;
  /** 值变化回调 */
  onChange: (value: Date | undefined) => void;
  /** 占位符 */
  placeholder?: string;
  /** 自定义类名 */
  className?: string;
}

export interface DateRangeFilterProps {
  /** 筛选器标签 */
  label: string;
  /** 当前值 */
  value?: DateRange;
  /** 值变化回调 */
  onChange: (value: DateRange | undefined) => void;
  /** 占位符 */
  placeholder?: string;
  /** 自定义类名 */
  className?: string;
}

// === 选择筛选器 ===

export function SelectFilter({
  label,
  value,
  options,
  onChange,
  placeholder = '全部',
  clearable = true,
  className,
}: SelectFilterProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="text-sm text-muted-foreground whitespace-nowrap">
        {label}:
      </span>
      <Select
        value={value ?? '__all__'}
        onValueChange={(v) => onChange(v === '__all__' ? undefined : v)}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">{placeholder}</SelectItem>
          {options.map((option) => (
            <SelectItem
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {clearable && value && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => onChange(undefined)}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

// === 日期筛选器 ===

export function DateFilter({
  label,
  value,
  onChange,
  placeholder = '选择日期',
  className,
}: DateFilterProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="text-sm text-muted-foreground whitespace-nowrap">
        {label}:
      </span>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              'w-[160px] justify-start text-left font-normal',
              !value && 'text-muted-foreground'
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {value ? format(value, 'yyyy-MM-dd', { locale: zhCN }) : placeholder}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={value}
            onSelect={onChange}
            locale={zhCN}
            initialFocus
          />
        </PopoverContent>
      </Popover>
      {value && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => onChange(undefined)}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

// === 日期范围筛选器 ===

export function DateRangeFilter({
  label,
  value,
  onChange,
  placeholder = '选择日期范围',
  className,
}: DateRangeFilterProps) {
  const displayText = React.useMemo(() => {
    if (!value?.from) return placeholder;
    if (!value.to) return format(value.from, 'yyyy-MM-dd', { locale: zhCN });
    return `${format(value.from, 'yyyy-MM-dd', { locale: zhCN })} ~ ${format(value.to, 'yyyy-MM-dd', { locale: zhCN })}`;
  }, [value, placeholder]);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="text-sm text-muted-foreground whitespace-nowrap">
        {label}:
      </span>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              'w-[240px] justify-start text-left font-normal',
              !value?.from && 'text-muted-foreground'
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {displayText}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="range"
            selected={value}
            onSelect={onChange}
            locale={zhCN}
            numberOfMonths={2}
            initialFocus
          />
        </PopoverContent>
      </Popover>
      {value?.from && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => onChange(undefined)}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

// === 筛选器容器 ===

interface FilterContainerProps {
  /** 子筛选器 */
  children: React.ReactNode;
  /** 激活的筛选器数量 */
  activeCount?: number;
  /** 清除所有筛选 */
  onClearAll?: () => void;
  /** 自定义类名 */
  className?: string;
}

export function FilterContainer({
  children,
  activeCount = 0,
  onClearAll,
  className,
}: FilterContainerProps) {
  return (
    <div className={cn('flex flex-wrap items-center gap-4', className)}>
      {children}
      {activeCount > 0 && onClearAll && (
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
          onClick={onClearAll}
        >
          <X className="mr-1 h-4 w-4" />
          清除筛选
          <Badge variant="secondary" className="ml-1">
            {activeCount}
          </Badge>
        </Button>
      )}
    </div>
  );
}

// === 导出 ===

export type { FilterOption, DateRange };
