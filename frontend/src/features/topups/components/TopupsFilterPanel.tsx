/**
 * Topups Filter Panel Component
 *
 * Filter controls for topup requests list
 * Extracted from TopupsPage.tsx for better maintainability
 */

'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { TopupStatus } from '../types';

export interface FilterState {
  status: TopupStatus | '';
  project_id: string;
  start_date: string;
  end_date: string;
  min_amount: string;
  max_amount: string;
}

export const initialFilterState: FilterState = {
  status: '',
  project_id: '',
  start_date: '',
  end_date: '',
  min_amount: '',
  max_amount: '',
};

interface TopupsFilterPanelProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onReset: () => void;
}

const statusOptions: { value: TopupStatus | ''; label: string }[] = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'pending_review', label: '待数据复核' },
  { value: 'finance_approve', label: '待财务终审' },
  { value: 'paid', label: '已支付' },
  { value: 'completed', label: '已完成' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'cancelled', label: '已取消' },
];

export function TopupsFilterPanel({
  filters,
  onFiltersChange,
  onReset,
}: TopupsFilterPanelProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <div className="space-y-2">
        <Label>状态筛选</Label>
        <Select
          value={filters.status}
          onValueChange={(value) =>
            onFiltersChange({ ...filters, status: value as TopupStatus | '' })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>开始日期</Label>
        <Input
          type="date"
          value={filters.start_date}
          onChange={(e) => onFiltersChange({ ...filters, start_date: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>结束日期</Label>
        <Input
          type="date"
          value={filters.end_date}
          onChange={(e) => onFiltersChange({ ...filters, end_date: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>最小金额(元)</Label>
        <Input
          type="number"
          placeholder="0"
          value={filters.min_amount}
          onChange={(e) => onFiltersChange({ ...filters, min_amount: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>最大金额(元)</Label>
        <Input
          type="number"
          placeholder="不限"
          value={filters.max_amount}
          onChange={(e) => onFiltersChange({ ...filters, max_amount: e.target.value })}
        />
      </div>

      <div className="flex items-end">
        <Button variant="outline" onClick={onReset} className="w-full">
          重置筛选
        </Button>
      </div>
    </div>
  );
}

export default TopupsFilterPanel;
