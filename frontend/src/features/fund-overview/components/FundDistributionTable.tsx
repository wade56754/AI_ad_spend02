/**
 * FundDistributionTable Component
 *
 * 资金分布表格（按项目/按渠道）
 *
 * SoT 对齐:
 * - A2-fund-overview.md §3.1: 页面布局
 *
 * @module features/fund-overview/components
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { ExternalLink } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { FundByProjectItem, FundByChannelItem, FundDistributionDimension } from '../types';

// ========== 辅助函数 ==========

/**
 * 格式化金额显示
 */
function formatCurrency(value: number): string {
  if (value === 0) return '¥0';
  const wan = value / 10000;
  if (Math.abs(wan) >= 1) {
    return `¥${wan.toFixed(1)}万`;
  }
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

// ========== 类型 ==========

interface FundDistributionTableProps {
  dimension: FundDistributionDimension;
  data: FundByProjectItem[] | FundByChannelItem[];
  loading?: boolean;
}

// ========== 组件 ==========

/**
 * 表格加载骨架屏
 */
function TableSkeleton({ rows = 5, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} className="h-10 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * 按项目的表格
 */
function ProjectTable({ data }: { data: FundByProjectItem[] }) {
  if (!data.length) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        暂无项目资金数据
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[50px]">#</TableHead>
          <TableHead>项目名称</TableHead>
          <TableHead>负责人</TableHead>
          <TableHead className="text-right">累计充值</TableHead>
          <TableHead className="text-right">累计消耗</TableHead>
          <TableHead className="text-right">余额</TableHead>
          <TableHead className="text-right">应收</TableHead>
          <TableHead className="text-right">已回款</TableHead>
          <TableHead className="w-[80px]">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((item, index) => (
          <TableRow key={item.project_id}>
            <TableCell className="font-medium text-muted-foreground">
              {index + 1}
            </TableCell>
            <TableCell className="font-medium">{item.project_name}</TableCell>
            <TableCell className="text-muted-foreground">{item.owner_name}</TableCell>
            <TableCell className="text-right text-green-600">
              {formatCurrency(item.total_topup)}
            </TableCell>
            <TableCell className="text-right text-blue-600">
              {formatCurrency(item.total_spend)}
            </TableCell>
            <TableCell className={cn(
              'text-right font-medium',
              item.balance < 0 ? 'text-red-600' : 'text-foreground'
            )}>
              {formatCurrency(item.balance)}
            </TableCell>
            <TableCell className="text-right text-orange-600">
              {formatCurrency(item.receivable)}
            </TableCell>
            <TableCell className="text-right text-purple-600">
              {formatCurrency(item.received)}
            </TableCell>
            <TableCell>
              <Link href={`/projects/${item.project_id}`}>
                <Button variant="ghost" size="sm">
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/**
 * 按渠道的表格
 */
function ChannelTable({ data }: { data: FundByChannelItem[] }) {
  if (!data.length) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        暂无渠道资金数据
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[50px]">#</TableHead>
          <TableHead>渠道名称</TableHead>
          <TableHead className="text-right">账户数</TableHead>
          <TableHead className="text-right">累计充值</TableHead>
          <TableHead className="text-right">累计消耗</TableHead>
          <TableHead className="text-right">余额</TableHead>
          <TableHead className="w-[80px]">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((item, index) => (
          <TableRow key={item.channel_id}>
            <TableCell className="font-medium text-muted-foreground">
              {index + 1}
            </TableCell>
            <TableCell className="font-medium">{item.channel_name}</TableCell>
            <TableCell className="text-right text-muted-foreground">
              {item.total_accounts}
            </TableCell>
            <TableCell className="text-right text-green-600">
              {formatCurrency(item.total_topup)}
            </TableCell>
            <TableCell className="text-right text-blue-600">
              {formatCurrency(item.total_spend)}
            </TableCell>
            <TableCell className={cn(
              'text-right font-medium',
              item.balance < 0 ? 'text-red-600' : 'text-foreground'
            )}>
              {formatCurrency(item.balance)}
            </TableCell>
            <TableCell>
              <Link href={`/channels/${item.channel_id}`}>
                <Button variant="ghost" size="sm">
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/**
 * 资金分布表格
 */
export function FundDistributionTable({
  dimension,
  data,
  loading = false,
}: FundDistributionTableProps) {
  if (loading) {
    return <TableSkeleton rows={5} cols={dimension === 'project' ? 9 : 7} />;
  }

  if (dimension === 'project') {
    return <ProjectTable data={data as FundByProjectItem[]} />;
  }

  return <ChannelTable data={data as FundByChannelItem[]} />;
}

export default FundDistributionTable;
