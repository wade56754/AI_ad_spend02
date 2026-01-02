/**
 * Settlement Rules Table Component
 *
 * Displays paginated list of settlement rules
 *
 * SoT: DATA_SCHEMA.md v5.6 §3.5.7 (settlement_rules entity)
 * SoT: BR-PROJ.md v1.0 (定价规则)
 */

'use client';

import { useState } from 'react';
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
import { MoreHorizontal, Edit, Trash2, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { useSettlementRules, useDeleteSettlementRule } from '../hooks';
import {
  type SettlementRule,
  type SettlementRuleListParams,
  RULE_TYPE_CONFIG,
  isTieredConfig,
  isMarkupConfig,
} from '../types';

interface SettlementRulesTableProps {
  onEdit?: (rule: SettlementRule) => void;
}

/**
 * 格式化规则配置为可读字符串
 */
function formatRuleConfig(rule: SettlementRule): string {
  if (isTieredConfig(rule.config)) {
    const tiers = rule.config.tiers;
    if (tiers.length === 0) return '-';
    if (tiers.length === 1) {
      return `¥${tiers[0].unit_price}/粉`;
    }
    return `${tiers.length} 个阶梯，¥${tiers[0].unit_price} - ¥${tiers[tiers.length - 1].unit_price}`;
  }

  if (isMarkupConfig(rule.config)) {
    const { markup_type, markup_value } = rule.config;
    if (markup_type === 'percentage') {
      return `加成 ${markup_value}%`;
    }
    return `加成 ¥${markup_value}`;
  }

  return '-';
}

export function SettlementRulesTable({ onEdit }: SettlementRulesTableProps) {
  const [params, setParams] = useState<SettlementRuleListParams>({
    page: 1,
    page_size: 20,
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<SettlementRule | null>(null);

  const { data, isLoading, error } = useSettlementRules(params);
  const deleteMutation = useDeleteSettlementRule({
    onSuccess: () => {
      toast.success('删除成功');
      setDeleteDialogOpen(false);
      setRuleToDelete(null);
    },
    onError: (error) => {
      toast.error(error.message || '删除失败');
    },
  });

  const handleDelete = (rule: SettlementRule) => {
    setRuleToDelete(rule);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (ruleToDelete) {
      deleteMutation.mutate(ruleToDelete.id);
    }
  };

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">加载中...</div>;
  }

  if (error) {
    return <div className="py-8 text-center text-destructive">加载失败: {error.message}</div>;
  }

  const rules = data?.items ?? [];
  const pagination = data?.meta;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>规则名称</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>配置详情</TableHead>
            <TableHead>生效日期</TableHead>
            <TableHead>状态</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rules.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            rules.map((rule) => (
              <TableRow key={rule.id}>
                <TableCell className="font-medium">{rule.name}</TableCell>
                <TableCell>
                  <Badge variant="outline">{RULE_TYPE_CONFIG[rule.rule_type].label}</Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">{formatRuleConfig(rule)}</TableCell>
                <TableCell>
                  <div className="text-sm">
                    <div>{rule.effective_from}</div>
                    {rule.effective_to && (
                      <div className="text-muted-foreground">至 {rule.effective_to}</div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  {rule.is_effective ? (
                    <Badge variant="default" className="gap-1">
                      <CheckCircle className="h-3 w-3" />
                      生效中
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="gap-1">
                      <XCircle className="h-3 w-3" />
                      未生效
                    </Badge>
                  )}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onEdit?.(rule)}>
                        <Edit className="mr-2 h-4 w-4" />
                        编辑
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleDelete(rule)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        删除
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            共 {pagination.total} 条，第 {pagination.page} / {pagination.total_pages} 页
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.total_pages}
            >
              下一页
            </Button>
          </div>
        </div>
      )}

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除规则「{ruleToDelete?.name}」吗？此操作不可撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? '删除中...' : '删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
