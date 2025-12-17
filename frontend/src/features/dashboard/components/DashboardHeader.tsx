/**
 * DashboardHeader Component
 *
 * Page header with title, subtitle and refresh button
 * Based on UI_DESIGN_SYSTEM.md v2.0
 *
 * Typography: H1 = text-3xl font-bold, Body = text-sm
 * Spacing: mb-6 (区块分隔)
 */

'use client';

import React from 'react';
import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DashboardHeaderProps {
  userName?: string;
  isRefreshing?: boolean;
  onRefresh?: () => void;
}

export function DashboardHeader({
  userName = '用户',
  isRefreshing = false,
  onRefresh,
}: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1
          className="text-3xl font-bold text-foreground"
          data-testid="dashboard-welcome-title"
        >
          欢迎回来，{userName}
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          这是您的系统概览，查看今日数据和待处理事项
        </p>
      </div>
      <Button
        variant="secondary"
        size="default"
        onClick={onRefresh}
        disabled={isRefreshing}
        data-testid="dashboard-refresh-button"
      >
        <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
        刷新
      </Button>
    </div>
  );
}

export default DashboardHeader;
