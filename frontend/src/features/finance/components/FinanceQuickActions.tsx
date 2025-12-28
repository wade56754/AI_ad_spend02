/**
 * FinanceQuickActions Component
 *
 * 快捷操作面板 - 从 FinancePage.tsx 提取
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  CreditCard,
  FileText,
  CheckCircle,
  PieChart,
} from 'lucide-react';

interface QuickAction {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  iconColor: string;
}

const quickActions: QuickAction[] = [
  { href: '/topups', icon: CreditCard, label: '充值管理', iconColor: 'text-blue-600' },
  { href: '/settlements', icon: FileText, label: '结算管理', iconColor: 'text-purple-600' },
  { href: '/reconciliation', icon: CheckCircle, label: '对账管理', iconColor: 'text-green-600' },
  { href: '/finance/profit', icon: PieChart, label: '利润分析', iconColor: 'text-orange-600' },
];

interface FinanceQuickActionsProps {
  className?: string;
}

export function FinanceQuickActions({ className }: FinanceQuickActionsProps) {
  return (
    <Card className={className} data-testid="finance-quick-actions">
      <CardHeader>
        <CardTitle>快捷操作</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link key={action.href} href={action.href}>
                <Button variant="outline" className="w-full h-auto py-4 flex flex-col items-center gap-2">
                  <Icon className={`h-6 w-6 ${action.iconColor}`} />
                  <span>{action.label}</span>
                </Button>
              </Link>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default FinanceQuickActions;
