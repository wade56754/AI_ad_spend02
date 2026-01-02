'use client';

/**
 * Commission Rules Table - 提成规则列表
 *
 * TASK-PRJ-003: 提成配置
 */

import { useState } from 'react';
import { MoreHorizontal, Calculator, Pencil, Trash2, Star } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { useDeleteCommissionRule, useSetAsDefault } from '../hooks';
import {
  type CommissionRule,
  getRuleStatus,
  COMMISSION_RULE_STATUS_CONFIG,
  formatTierRange,
  formatCommissionAmount,
} from '../types';

interface CommissionRulesTableProps {
  data: CommissionRule[];
  isLoading: boolean;
  error: Error | null;
  onEdit: (rule: CommissionRule) => void;
  onCalculate: (rule: CommissionRule) => void;
}

export function CommissionRulesTable({
  data,
  isLoading,
  error,
  onEdit,
  onCalculate,
}: CommissionRulesTableProps) {
  const [deleteTarget, setDeleteTarget] = useState<CommissionRule | null>(null);

  const deleteMutation = useDeleteCommissionRule();
  const setDefaultMutation = useSetAsDefault();

  const handleDelete = () => {
    if (deleteTarget) {
      deleteMutation.mutate(deleteTarget.id, {
        onSuccess: () => setDeleteTarget(null),
      });
    }
  };

  if (isLoading) {
    return <TableSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        加载失败: {error.message}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">
        暂无提成规则，点击"新建规则"创建第一个
      </div>
    );
  }

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>规则名称</TableHead>
              <TableHead>阶梯配置</TableHead>
              <TableHead>生效期间</TableHead>
              <TableHead>状态</TableHead>
              <TableHead className="w-[100px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((rule) => {
              const status = getRuleStatus(rule);
              const statusConfig = COMMISSION_RULE_STATUS_CONFIG[status];

              return (
                <TableRow key={rule.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{rule.name}</span>
                      {rule.is_default && (
                        <Badge variant="secondary" className="gap-1">
                          <Star className="h-3 w-3" />
                          默认
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <TierBadges tiers={rule.config.tiers} />
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      <div>{rule.effective_from}</div>
                      <div className="text-muted-foreground">至 {rule.effective_to ?? '永久'}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        statusConfig.color === 'success'
                          ? 'default'
                          : statusConfig.color === 'warning'
                            ? 'secondary'
                            : 'outline'
                      }
                    >
                      {statusConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onCalculate(rule)}>
                          <Calculator className="mr-2 h-4 w-4" />
                          计算提成
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onEdit(rule)}>
                          <Pencil className="mr-2 h-4 w-4" />
                          编辑
                        </DropdownMenuItem>
                        {!rule.is_default && (
                          <DropdownMenuItem
                            onClick={() => setDefaultMutation.mutate(rule.id)}
                            disabled={setDefaultMutation.isPending}
                          >
                            <Star className="mr-2 h-4 w-4" />
                            设为默认
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => setDeleteTarget(rule)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          删除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除提成规则 "{deleteTarget?.name}"
              吗？此操作将设置规则的结束日期，已关联的项目将不再使用此规则。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

// ========== Sub Components ==========

function TierBadges({ tiers }: { tiers: CommissionRule['config']['tiers'] }) {
  // Show first 2 tiers, then "+N more" if more exist
  const displayTiers = tiers.slice(0, 2);
  const remaining = tiers.length - 2;

  return (
    <div className="flex flex-wrap gap-1">
      {displayTiers.map((tier, index) => (
        <Badge key={index} variant="outline" className="text-xs">
          {formatTierRange(tier)}: {formatCommissionAmount(tier.rate)}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="outline" className="text-xs text-muted-foreground">
          +{remaining} 阶梯
        </Badge>
      )}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>规则名称</TableHead>
            <TableHead>阶梯配置</TableHead>
            <TableHead>生效期间</TableHead>
            <TableHead>状态</TableHead>
            <TableHead className="w-[100px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {[1, 2, 3].map((i) => (
            <TableRow key={i}>
              <TableCell>
                <Skeleton className="h-5 w-32" />
              </TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Skeleton className="h-5 w-20" />
                  <Skeleton className="h-5 w-20" />
                </div>
              </TableCell>
              <TableCell>
                <Skeleton className="h-5 w-24" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-5 w-16" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-8 w-8" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
