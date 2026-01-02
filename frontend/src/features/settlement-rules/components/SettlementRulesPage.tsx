/**
 * Settlement Rules Page Component
 *
 * Main page for settlement rule (pricing configuration) management
 *
 * SoT: DATA_SCHEMA.md v5.6 §3.5.7 (settlement_rules entity)
 * SoT: BR-PROJ.md v1.0 (定价规则)
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { SettlementRulesTable } from './SettlementRulesTable';
import { SettlementRuleDialog } from './SettlementRuleDialog';
import type { SettlementRule } from '../types';

export function SettlementRulesPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<SettlementRule | null>(null);

  const handleCreate = () => {
    setEditingRule(null);
    setDialogOpen(true);
  };

  const handleEdit = (rule: SettlementRule) => {
    setEditingRule(rule);
    setDialogOpen(true);
  };

  const handleDialogClose = (open: boolean) => {
    setDialogOpen(open);
    if (!open) {
      setEditingRule(null);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">定价配置</h1>
          <p className="text-muted-foreground">管理结算规则，支持阶梯计价和加成计价两种模式</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          新建规则
        </Button>
      </div>

      <SettlementRulesTable onEdit={handleEdit} />

      <SettlementRuleDialog rule={editingRule} open={dialogOpen} onOpenChange={handleDialogClose} />
    </div>
  );
}
