/**
 * AccountOverviewCard Component
 *
 * Shows account statistics summary
 * Based on UI_DESIGN_SYSTEM.md v2.0
 *
 * Card: shadcn Card, rounded-xl
 * Typography: H3 = text-xl font-semibold
 * Colors: text-foreground, text-muted-foreground, text-green-500 (成功)
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

interface AccountOverviewCardProps {
  activeProjects: number;
  activeAccounts: number;
  totalBalance: number;
}

export function AccountOverviewCard({
  activeProjects,
  activeAccounts,
  totalBalance,
}: AccountOverviewCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  return (
    <Card className="rounded-xl border shadow-sm" data-testid="dashboard-account-overview">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-semibold text-foreground">
          账户概览
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-0">
          <div className="flex items-center justify-between py-3">
            <span className="text-sm text-muted-foreground">活跃项目</span>
            <span className="text-lg font-semibold text-foreground">
              {activeProjects}
            </span>
          </div>
          <Separator />
          <div className="flex items-center justify-between py-3">
            <span className="text-sm text-muted-foreground">广告账户</span>
            <span className="text-lg font-semibold text-foreground">
              {activeAccounts}
            </span>
          </div>
          <Separator />
          <div className="flex items-center justify-between py-3">
            <span className="text-sm text-muted-foreground">账户余额</span>
            <span className="text-lg font-semibold text-green-500">
              {formatCurrency(totalBalance)}
            </span>
          </div>
        </div>
        <Button variant="ghost" className="w-full mt-4 text-primary" asChild>
          <Link href="/ledger" className="flex items-center justify-center gap-2">
            查看账本明细
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}

export default AccountOverviewCard;
