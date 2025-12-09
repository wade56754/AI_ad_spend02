/**
 * QuickActionsCard Component
 *
 * Quick action buttons for common tasks
 * Based on UI_DESIGN_SYSTEM.md v2.0
 *
 * Card: shadcn Card, rounded-xl
 * Typography: H3 = text-xl font-semibold
 * Colors: 图表颜色规范 (blue, green, violet, amber)
 */

'use client';

import React from 'react';
import Link from 'next/link';
import {
  FileText,
  PlusCircle,
  Upload,
  CheckCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { QuickAction } from '../types';

const ICON_MAP: Record<string, React.ReactNode> = {
  'file-plus': <FileText className="h-5 w-5" />,
  'plus-circle': <PlusCircle className="h-5 w-5" />,
  upload: <Upload className="h-5 w-5" />,
  'check-square': <CheckCircle className="h-5 w-5" />,
};

// 对齐 UI_DESIGN_SYSTEM.md 2.4 图表颜色
const COLOR_CLASSES: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-500',
  green: 'bg-green-100 text-green-500',
  purple: 'bg-violet-100 text-violet-500',
  orange: 'bg-amber-100 text-amber-500',
};

interface QuickActionsCardProps {
  actions: QuickAction[];
}

export function QuickActionsCard({ actions }: QuickActionsCardProps) {
  return (
    <Card className="rounded-xl border shadow-sm" data-testid="dashboard-quick-actions">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-semibold text-foreground">
          快捷操作
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {actions.map((action) => (
            <Link
              key={action.id}
              href={action.href}
              className="flex flex-col items-center gap-3 p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors"
            >
              <div className={cn('p-3 rounded-full', COLOR_CLASSES[action.color] || COLOR_CLASSES.blue)}>
                {ICON_MAP[action.icon] || <FileText className="h-5 w-5" />}
              </div>
              <span className="text-sm font-medium text-foreground">{action.label}</span>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default QuickActionsCard;
