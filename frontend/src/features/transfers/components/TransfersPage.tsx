/**
 * Transfers Page Component
 *
 * Main page for transfer request management
 * SoT 对齐: STATE_MACHINE.md v2.6 第12章
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { TransfersTable } from './TransfersTable';
import { TransferForm } from './TransferForm';

export function TransfersPage() {
  const [formOpen, setFormOpen] = useState(false);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">余额迁移</h1>
          <p className="text-muted-foreground">管理死号余额迁移申请</p>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          新建迁移申请
        </Button>
      </div>

      <TransfersTable />
      <TransferForm open={formOpen} onOpenChange={setFormOpen} />
    </div>
  );
}
