/**
 * PendingTasksCard Component
 *
 * Shows pending items that need attention
 * Based on UI_DESIGN_SYSTEM.md v2.0
 *
 * Card: shadcn Card, rounded-xl
 * Typography: H3 = text-xl font-semibold, Body = text-sm
 * Status colors: warning (orange) for pending, success (green) for done
 */

'use client';

import React from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  CreditCard,
  Wallet,
  CheckCircle,
  FileText,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { PendingTask } from '../types';

interface PendingItemProps {
  title: string;
  count: number;
  href: string;
  icon: React.ReactNode;
  priority?: 'high' | 'medium' | 'low';
}

const PRIORITY_STYLES = {
  high: {
    badge: 'bg-red-100 text-red-800 border-red-200',
    label: '高优先级',
  },
  medium: {
    badge: 'bg-orange-100 text-orange-800 border-orange-200',
    label: '中优先级',
  },
  low: {
    badge: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    label: '低优先级',
  },
};

function PendingItem({ title, count, href, icon, priority = 'medium' }: PendingItemProps) {
  const priorityStyle = PRIORITY_STYLES[priority];

  return (
    <Link
      href={href}
      className="flex items-center justify-between p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors"
    >
      <div className="flex items-center gap-3">
        <div className="p-2 bg-background rounded-lg text-muted-foreground">{icon}</div>
        <div className="flex flex-col">
          <span className="text-sm font-medium text-foreground">{title}</span>
          {count > 0 && (
            <span className="text-xs text-muted-foreground">{priorityStyle.label}</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge
          variant={count > 0 ? 'warning' : 'success'}
          className={cn(
            'px-2 py-0.5 text-xs font-semibold',
            count > 0
              ? priorityStyle.badge
              : 'bg-green-100 text-green-800 border-green-200'
          )}
        >
          {count}
        </Badge>
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
      </div>
    </Link>
  );
}

const ICON_MAP: Record<string, React.ReactNode> = {
  'credit-card': <CreditCard className="h-5 w-5" />,
  wallet: <Wallet className="h-5 w-5" />,
  'check-circle': <CheckCircle className="h-5 w-5" />,
  'file-text': <FileText className="h-5 w-5" />,
};

interface PendingTasksCardProps {
  tasks: PendingTask[];
}

export function PendingTasksCard({ tasks }: PendingTasksCardProps) {
  return (
    <Card className="rounded-xl border shadow-sm" data-testid="dashboard-pending-tasks">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-semibold text-foreground">
          待处理事项
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {tasks.map((task) => (
            <PendingItem
              key={task.id}
              title={task.title}
              count={task.count}
              href={task.href}
              priority={task.priority}
              icon={task.icon ? ICON_MAP[task.icon] || <FileText className="h-5 w-5" /> : <FileText className="h-5 w-5" />}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default PendingTasksCard;
