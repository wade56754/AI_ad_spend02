/**
 * Top Lists Component
 *
 * SoT: docs/10.module-specs/A1-dashboard.md §3.2 组件清单
 *
 * 展示 Top N 计划列表：
 * 1. 今日消耗 Top 5 计划
 * 2. ROAS 最差 Top 5 计划
 *
 * 打通"趋势 → 归因对象 → 行动"闭环
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ExternalLink, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { formatCurrency, formatNumber } from '../utils/formatters';

export interface CampaignData {
  id: string;
  name: string;
  accountName: string;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  roas: number;
  status: 'active' | 'paused' | 'pending';
}

interface TopListsProps {
  topSpendCampaigns: CampaignData[];
  worstROASCampaigns: CampaignData[];
  className?: string;
}

const STATUS_CONFIG = {
  active: { label: '投放中', variant: 'default' as const, color: 'bg-green-500' },
  paused: { label: '已暂停', variant: 'secondary' as const, color: 'bg-gray-500' },
  pending: { label: '待审核', variant: 'outline' as const, color: 'bg-yellow-500' },
};

function CampaignTable({
  campaigns,
  sortBy,
  tableTestId,
}: {
  campaigns: CampaignData[];
  sortBy: 'spend' | 'roas';
  tableTestId?: string;
}) {
  const router = useRouter();
  if (campaigns.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>当前筛选条件下暂无数据</p>
        <Button variant="link" size="sm" className="mt-2">
          调整筛选条件
        </Button>
      </div>
    );
  }

  return (
    <ScrollArea className="w-full">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[40px]">#</TableHead>
            <TableHead>计划名称</TableHead>
            <TableHead>所属账户</TableHead>
            <TableHead className="text-right">消耗</TableHead>
            <TableHead className="text-right">展现</TableHead>
            <TableHead className="text-right">点击</TableHead>
            <TableHead className="text-right">转化</TableHead>
            <TableHead className="text-right">ROAS</TableHead>
            <TableHead className="text-center">状态</TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {campaigns.map((campaign, index) => {
            const statusConfig = STATUS_CONFIG[campaign.status];
            const roasColor =
              campaign.roas >= 1.8
                ? 'text-green-600'
                : campaign.roas >= 1.2
                ? 'text-yellow-600'
                : 'text-red-600';

            // Phase 1: 异常项目高亮但可点击
            const isAbnormal = campaign.roas < 1.0;
            const rowWarningClass = isAbnormal
              ? 'bg-amber-50 dark:bg-amber-950/20 hover:bg-amber-100 dark:hover:bg-amber-950/30'
              : 'hover:bg-muted/50';

            return (
              <TableRow
                key={campaign.id}
                className={`${rowWarningClass} cursor-pointer transition-colors`}
                data-testid={tableTestId ? `top-item-${index}` : undefined}
                onClick={() => router.push(`/projects/${campaign.id}`)}
              >
                <TableCell className="font-medium text-muted-foreground">
                  {index + 1}
                </TableCell>
                <TableCell className="font-medium max-w-[200px] truncate">
                  {campaign.name}
                </TableCell>
                <TableCell className="text-muted-foreground">{campaign.accountName}</TableCell>
                <TableCell className="text-right font-mono">
                  {formatCurrency(campaign.spend, 0)}
                </TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {formatNumber(campaign.impressions)}
                </TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {formatNumber(campaign.clicks)}
                </TableCell>
                <TableCell className="text-right font-medium">
                  {formatNumber(campaign.conversions)}
                </TableCell>
                <TableCell className={`text-right font-semibold ${roasColor}`}>
                  {(Number(campaign.roas) || 0).toFixed(2)}
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant={statusConfig.variant}>
                    <div className={`w-1.5 h-1.5 rounded-full mr-1.5 ${statusConfig.color}`} />
                    {statusConfig.label}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Link href={`/projects/${campaign.id}`}>
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <ScrollBar orientation="horizontal" />
    </ScrollArea>
  );
}

export function TopLists({
  topSpendCampaigns,
  worstROASCampaigns,
  className,
}: TopListsProps) {
  return (
    <div className={`grid grid-cols-1 gap-6 ${className || ''}`} data-testid="top-lists">
      {/* 今日消耗 Top N */}
      <Card data-testid="top-spend">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            今日消耗 Top 5 计划
          </CardTitle>
          <Link href="/projects?sort=spend&order=desc">
            <Button variant="ghost" size="sm">
              查看全部
              <ExternalLink className="h-3.5 w-3.5 ml-1.5" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          <CampaignTable campaigns={topSpendCampaigns} sortBy="spend" tableTestId="top-spend" />
        </CardContent>
      </Card>

      {/* ROAS 最差 Top N */}
      <Card data-testid="worst-roas">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <TrendingDown className="h-5 w-5 text-red-600" />
            ROAS 最差 Top 5 计划
          </CardTitle>
          <Link href="/projects?sort=roas&order=asc">
            <Button variant="ghost" size="sm">
              查看全部
              <ExternalLink className="h-3.5 w-3.5 ml-1.5" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          <CampaignTable campaigns={worstROASCampaigns} sortBy="roas" tableTestId="worst-roas" />
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * 生成模拟 Top 列表数据
 * TODO: 替换为实际 API 调用
 */
export function generateMockTopLists(): {
  topSpend: CampaignData[];
  worstROAS: CampaignData[];
} {
  const mockCampaigns: CampaignData[] = [
    {
      id: 'camp001',
      name: '618大促-爆款商品A',
      accountName: 'FB-品牌主账户',
      spend: 45680,
      impressions: 2350000,
      clicks: 12500,
      conversions: 856,
      roas: 2.35,
      status: 'active',
    },
    {
      id: 'camp002',
      name: '新品上市-智能手表系列',
      accountName: 'Google-搜索广告',
      spend: 38920,
      impressions: 1890000,
      clicks: 9800,
      conversions: 645,
      roas: 1.92,
      status: 'active',
    },
    {
      id: 'camp003',
      name: '夏季清仓-服饰专场',
      accountName: 'TikTok-A类视频',
      spend: 32150,
      impressions: 3200000,
      clicks: 15600,
      conversions: 423,
      roas: 0.85,
      status: 'active',
    },
    {
      id: 'camp004',
      name: '品牌曝光-视频广告',
      accountName: 'FB-ROI优化组',
      spend: 28900,
      impressions: 5600000,
      clicks: 8900,
      conversions: 289,
      roas: 0.62,
      status: 'paused',
    },
    {
      id: 'camp005',
      name: '精准转化-搜索关键词',
      accountName: 'Google-搜索广告',
      spend: 25400,
      impressions: 890000,
      clicks: 7200,
      conversions: 512,
      roas: 2.15,
      status: 'active',
    },
    {
      id: 'camp006',
      name: '再营销-老客唤醒',
      accountName: 'FB-品牌主账户',
      spend: 18500,
      impressions: 1200000,
      clicks: 5400,
      conversions: 156,
      roas: 0.48,
      status: 'active',
    },
  ];

  // 按消耗排序 Top 5
  const topSpend = [...mockCampaigns].sort((a, b) => b.spend - a.spend).slice(0, 5);

  // 按 ROAS 排序（最差）Top 5
  const worstROAS = [...mockCampaigns].sort((a, b) => a.roas - b.roas).slice(0, 5);

  return {
    topSpend,
    worstROAS,
  };
}
