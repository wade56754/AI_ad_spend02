/**
 * QuickActions Component
 *
 * SoT: docs/10.module-specs/A1-dashboard.md
 * CodeBlock: CB-FE-004 (ActionButtons)
 *
 * 功能: 快捷操作按钮组
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Plus, FileText, Wallet } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface QuickActionsProps {
  className?: string;
}

/**
 * 快捷操作按钮组
 */
export function QuickActions({ className }: QuickActionsProps) {
  return (
    <div className={"flex gap-3" + (className ? " " + className : "")}>
      <Link href="/projects/new">
        <Button className="shadow-sm">
          <Plus className="h-4 w-4 mr-2" />
          创建新推广计划
        </Button>
      </Link>
      <Link href="/reports">
        <Button variant="outline" className="shadow-sm">
          <FileText className="h-4 w-4 mr-2" />
          查看报表
        </Button>
      </Link>
      <Link href="/finance">
        <Button variant="outline" className="shadow-sm">
          <Wallet className="h-4 w-4 mr-2" />
          财务中心
        </Button>
      </Link>
    </div>
  );
}

export default QuickActions;
