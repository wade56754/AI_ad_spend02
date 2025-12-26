/**
 * AdAccountsActions Component
 *
 * 操作工具栏 - 批量操作和数据导入导出
 * 从 AdAccountsPageV2.tsx 提取
 */

'use client';

import React from 'react';
import {
  RefreshCw,
  Download,
  Upload,
  Pause,
  Users,
  Archive,
  Columns3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export interface ColumnVisibility {
  accountName: boolean;
  buyer: boolean;
  supplier: boolean;
  todaySpend: boolean;
  monthSpend: boolean;
  feeRate: boolean;
  region: boolean;
}

export interface AdAccountsActionsProps {
  selectedCount: number;
  onRefresh: () => void;
  onExport: () => void;
  onImport: () => void;
  onBatchPause?: () => void;
  onBatchAssign?: () => void;
  onBatchArchive?: () => void;
  columnVisibility?: ColumnVisibility;
  onColumnVisibilityChange?: (key: keyof ColumnVisibility, visible: boolean) => void;
  className?: string;
}

const DEFAULT_COLUMN_VISIBILITY: ColumnVisibility = {
  accountName: true,
  buyer: true,
  supplier: true,
  todaySpend: true,
  monthSpend: true,
  feeRate: false,
  region: false,
};

export function AdAccountsActions({
  selectedCount,
  onRefresh,
  onExport,
  onImport,
  onBatchPause,
  onBatchAssign,
  onBatchArchive,
  columnVisibility = DEFAULT_COLUMN_VISIBILITY,
  onColumnVisibilityChange,
  className,
}: AdAccountsActionsProps) {
  return (
    <div className={`flex items-center justify-between ${className || ''}`} data-testid="ad-accounts-actions">
      {/* 左侧：批量操作 */}
      <div className="flex items-center gap-2">
        {selectedCount > 0 ? (
          <>
            <span className="text-sm text-gray-600">
              已选择 <span className="font-medium text-blue-600">{selectedCount}</span> 个账户
            </span>
            {onBatchPause && (
              <Button variant="outline" size="sm" onClick={onBatchPause}>
                <Pause className="w-4 h-4 mr-1" />
                批量暂停
              </Button>
            )}
            {onBatchAssign && (
              <Button variant="outline" size="sm" onClick={onBatchAssign}>
                <Users className="w-4 h-4 mr-1" />
                批量分配
              </Button>
            )}
            {onBatchArchive && (
              <Button
                variant="outline"
                size="sm"
                className="text-red-600 hover:text-red-700"
                onClick={onBatchArchive}
              >
                <Archive className="w-4 h-4 mr-1" />
                批量归档
              </Button>
            )}
          </>
        ) : (
          <span className="text-sm text-gray-500">
            提示：勾选账户可进行批量操作
          </span>
        )}
      </div>

      {/* 右侧：工具按钮 */}
      <div className="flex items-center gap-2">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="sm" onClick={onRefresh}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>刷新数据</TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <Button variant="outline" size="sm" onClick={onImport}>
          <Upload className="w-4 h-4 mr-1" />
          导入
        </Button>

        <Button variant="outline" size="sm" onClick={onExport}>
          <Download className="w-4 h-4 mr-1" />
          导出
        </Button>

        {/* 列配置 */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <Columns3 className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>显示列</DropdownMenuLabel>
            <DropdownMenuCheckboxItem
              checked={columnVisibility.accountName}
              onCheckedChange={(checked) => onColumnVisibilityChange?.('accountName', checked)}
            >
              账户名称
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={columnVisibility.buyer}
              onCheckedChange={(checked) => onColumnVisibilityChange?.('buyer', checked)}
            >
              投手
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={columnVisibility.supplier}
              onCheckedChange={(checked) => onColumnVisibilityChange?.('supplier', checked)}
            >
              代理商
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={columnVisibility.todaySpend}
              onCheckedChange={(checked) => onColumnVisibilityChange?.('todaySpend', checked)}
            >
              今日消耗
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={columnVisibility.monthSpend}
              onCheckedChange={(checked) => onColumnVisibilityChange?.('monthSpend', checked)}
            >
              本月消耗
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={columnVisibility.feeRate}
              onCheckedChange={(checked) => onColumnVisibilityChange?.('feeRate', checked)}
            >
              费率
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={columnVisibility.region}
              onCheckedChange={(checked) => onColumnVisibilityChange?.('region', checked)}
            >
              地区
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

export default AdAccountsActions;
