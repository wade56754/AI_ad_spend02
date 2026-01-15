'use client';

/**
 * 预付款管理面板
 *
 * TASK-PRJ-005: 三本账体系 - 预付款账本
 * SoT: BR-FIN-004 预收款≠收入（履约完成前是负债）
 *
 * @module features/projects/components
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import { toast } from 'sonner';
import {
  Plus,
  RotateCcw,
  Wallet,
  ArrowDownCircle,
  ArrowUpCircle,
  RefreshCw,
  Calendar,
  FileText,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import {
  usePrepaymentBalance,
  usePrepaymentEntries,
  useCreatePrepayment,
  useCreatePrepaymentReversal,
} from '../hooks';
import type { PrepaymentEntry, PrepaymentEntryType } from '../types';
import { PREPAYMENT_ENTRY_TYPE_CONFIG } from '../types';

// ========== Validation Schemas ==========

const prepaymentCreateSchema = z.object({
  amount: z.coerce.number().positive('金额必须为正数').max(100000000, '单笔入账不能超过 1 亿'),
  entry_date: z.string().min(1, '请选择入账日期'),
  notes: z.string().max(500, '备注不能超过 500 字').optional(),
});

const prepaymentReversalSchema = z.object({
  reference_id: z.coerce.number().positive('请选择要红冲的记录'),
  amount: z.coerce.number().negative('红冲金额必须为负数').min(-100000000, '单笔红冲不能超过 1 亿'),
  entry_date: z.string().min(1, '请选择红冲日期'),
  notes: z.string().min(1, '红冲原因为必填').max(500, '备注不能超过 500 字'),
});

type PrepaymentCreateValues = z.infer<typeof prepaymentCreateSchema>;
type PrepaymentReversalValues = z.infer<typeof prepaymentReversalSchema>;

// ========== Helper Functions ==========

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDate(dateString: string): string {
  try {
    return format(new Date(dateString), 'yyyy-MM-dd');
  } catch {
    return dateString;
  }
}

function _formatDateTime(dateString: string): string {
  try {
    return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
  } catch {
    return dateString;
  }
}

// ========== Sub-Components ==========

function BalanceCard({
  balance,
  totalTopup,
  totalReversal,
  entryCount,
  lastEntryDate,
  isLoading,
}: {
  balance?: number;
  totalTopup?: number;
  totalReversal?: number;
  entryCount?: number;
  lastEntryDate?: string | null;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-4" />
          <div className="grid grid-cols-3 gap-4">
            <Skeleton className="h-12" />
            <Skeleton className="h-12" />
            <Skeleton className="h-12" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Wallet className="h-5 w-5 text-primary" />
            预付款余额
          </CardTitle>
          {lastEntryDate && (
            <span className="text-xs text-muted-foreground">
              最后入账: {formatDate(lastEntryDate)}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold mb-4 text-primary">{formatCurrency(balance ?? 0)}</div>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground">
              <ArrowDownCircle className="h-4 w-4 text-green-500" />
              累计入账
            </div>
            <div className="font-medium text-green-600">{formatCurrency(totalTopup ?? 0)}</div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground">
              <ArrowUpCircle className="h-4 w-4 text-red-500" />
              累计红冲
            </div>
            <div className="font-medium text-red-600">
              {formatCurrency(Math.abs(totalReversal ?? 0))}
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground">
              <FileText className="h-4 w-4" />
              流水记录
            </div>
            <div className="font-medium">{entryCount ?? 0} 条</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function EntryTypeBadge({ type }: { type: PrepaymentEntryType }) {
  const config = PREPAYMENT_ENTRY_TYPE_CONFIG[type];
  return (
    <Badge variant={config.variant === 'success' ? 'default' : 'destructive'}>
      {type === 'TOPUP' && <ArrowDownCircle className="h-3 w-3 mr-1" />}
      {type === 'REVERSAL' && <ArrowUpCircle className="h-3 w-3 mr-1" />}
      {config.label}
    </Badge>
  );
}

function PrepaymentTable({
  entries,
  isLoading,
  onSelectForReversal,
}: {
  entries: PrepaymentEntry[];
  isLoading: boolean;
  onSelectForReversal?: (entry: PrepaymentEntry) => void;
}) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Wallet className="h-12 w-12 mx-auto mb-2 opacity-50" />
        <p>暂无预付款记录</p>
        <p className="text-sm">点击"入账"按钮添加第一笔预付款</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">类型</TableHead>
          <TableHead>入账日期</TableHead>
          <TableHead className="text-right">金额</TableHead>
          <TableHead className="text-right">余额</TableHead>
          <TableHead>操作人</TableHead>
          <TableHead>备注</TableHead>
          <TableHead className="w-[80px]">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {entries.map((entry) => (
          <TableRow key={entry.id}>
            <TableCell>
              <EntryTypeBadge type={entry.entry_type} />
            </TableCell>
            <TableCell>{formatDate(entry.entry_date)}</TableCell>
            <TableCell
              className={`text-right font-medium ${
                entry.entry_type === 'TOPUP' ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {entry.entry_type === 'TOPUP' ? '+' : ''}
              {formatCurrency(entry.amount)}
            </TableCell>
            <TableCell className="text-right">{formatCurrency(entry.balance_after)}</TableCell>
            <TableCell>{entry.operator_name ?? '-'}</TableCell>
            <TableCell className="max-w-[200px] truncate" title={entry.notes ?? ''}>
              {entry.notes ?? '-'}
            </TableCell>
            <TableCell>
              {entry.entry_type === 'TOPUP' && onSelectForReversal && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onSelectForReversal(entry)}
                  title="红冲此记录"
                >
                  <RotateCcw className="h-4 w-4" />
                </Button>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

// ========== Main Component ==========

interface PrepaymentPanelProps {
  projectId: number;
  projectName?: string;
}

export function PrepaymentPanel({ projectId, projectName }: PrepaymentPanelProps) {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isReversalOpen, setIsReversalOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<PrepaymentEntry | null>(null);
  const [page, setPage] = useState(1);
  const [entryTypeFilter, setEntryTypeFilter] = useState<string>('__all__');

  // Queries
  const { data: balanceData, isLoading: isBalanceLoading } = usePrepaymentBalance(projectId);
  const {
    data: entriesData,
    isLoading: isEntriesLoading,
    refetch: refetchEntries,
  } = usePrepaymentEntries(projectId, {
    page,
    page_size: 10,
    entry_type:
      entryTypeFilter === '__all__' ? undefined : (entryTypeFilter as PrepaymentEntryType),
  });

  // Mutations
  const createMutation = useCreatePrepayment({
    onSuccess: () => {
      toast.success('预付款入账成功');
      setIsCreateOpen(false);
      createForm.reset();
    },
    onError: (error) => {
      toast.error(error.message || '入账失败');
    },
  });

  const reversalMutation = useCreatePrepaymentReversal({
    onSuccess: () => {
      toast.success('红冲成功');
      setIsReversalOpen(false);
      setSelectedEntry(null);
      reversalForm.reset();
    },
    onError: (error) => {
      toast.error(error.message || '红冲失败');
    },
  });

  // Forms
  const createForm = useForm<PrepaymentCreateValues>({
    resolver: zodResolver(prepaymentCreateSchema),
    defaultValues: {
      amount: undefined,
      entry_date: format(new Date(), 'yyyy-MM-dd'),
      notes: '',
    },
  });

  const reversalForm = useForm<PrepaymentReversalValues>({
    resolver: zodResolver(prepaymentReversalSchema),
    defaultValues: {
      reference_id: undefined,
      amount: undefined,
      entry_date: format(new Date(), 'yyyy-MM-dd'),
      notes: '',
    },
  });

  // Handlers
  const handleCreate = (values: PrepaymentCreateValues) => {
    createMutation.mutate({
      projectId,
      input: values,
    });
  };

  const handleReversal = (values: PrepaymentReversalValues) => {
    reversalMutation.mutate({
      projectId,
      input: values,
    });
  };

  const handleSelectForReversal = (entry: PrepaymentEntry) => {
    setSelectedEntry(entry);
    reversalForm.reset({
      reference_id: entry.id,
      amount: -entry.amount, // 默认全额红冲
      entry_date: format(new Date(), 'yyyy-MM-dd'),
      notes: `红冲入账记录 #${entry.id}`,
    });
    setIsReversalOpen(true);
  };

  const balance = balanceData?.data;
  const entries = entriesData?.data ?? [];
  const pagination = entriesData?.meta?.pagination;

  return (
    <div className="space-y-6">
      {/* 余额卡片 */}
      <BalanceCard
        balance={balance?.balance}
        totalTopup={balance?.total_topup}
        totalReversal={balance?.total_reversal}
        entryCount={balance?.entry_count}
        lastEntryDate={balance?.last_entry_date}
        isLoading={isBalanceLoading}
      />

      {/* 流水列表 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">预付款流水</CardTitle>
              <CardDescription>
                {projectName ? `${projectName} 的` : ''}客户预付款入账与红冲记录
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Select value={entryTypeFilter} onValueChange={setEntryTypeFilter}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="全部类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">全部类型</SelectItem>
                  <SelectItem value="TOPUP">入账</SelectItem>
                  <SelectItem value="REVERSAL">红冲</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="icon" onClick={() => refetchEntries()}>
                <RefreshCw className="h-4 w-4" />
              </Button>

              {/* 入账对话框 */}
              <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    入账
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>新增预付款入账</DialogTitle>
                    <DialogDescription>
                      记录客户的预付款收款。入账后会自动更新项目预付款余额。
                    </DialogDescription>
                  </DialogHeader>
                  <Form {...createForm}>
                    <form onSubmit={createForm.handleSubmit(handleCreate)} className="space-y-4">
                      <FormField
                        control={createForm.control}
                        name="amount"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>入账金额</FormLabel>
                            <FormControl>
                              <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                                  ¥
                                </span>
                                <Input
                                  type="number"
                                  step="0.01"
                                  min="0.01"
                                  placeholder="0.00"
                                  className="pl-8"
                                  {...field}
                                />
                              </div>
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={createForm.control}
                        name="entry_date"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>入账日期</FormLabel>
                            <FormControl>
                              <div className="relative">
                                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input type="date" className="pl-10" {...field} />
                              </div>
                            </FormControl>
                            <FormDescription>不能晚于今天</FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={createForm.control}
                        name="notes"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>备注（可选）</FormLabel>
                            <FormControl>
                              <Textarea placeholder="例如：客户银行转账、微信收款等" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <DialogFooter>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setIsCreateOpen(false)}
                        >
                          取消
                        </Button>
                        <Button type="submit" disabled={createMutation.isPending}>
                          {createMutation.isPending ? '提交中...' : '确认入账'}
                        </Button>
                      </DialogFooter>
                    </form>
                  </Form>
                </DialogContent>
              </Dialog>

              {/* 红冲对话框 */}
              <Dialog open={isReversalOpen} onOpenChange={setIsReversalOpen}>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>预付款红冲</DialogTitle>
                    <DialogDescription>
                      红冲错误的入账记录。红冲金额会从余额中扣除。
                    </DialogDescription>
                  </DialogHeader>
                  <Form {...reversalForm}>
                    <form
                      onSubmit={reversalForm.handleSubmit(handleReversal)}
                      className="space-y-4"
                    >
                      {selectedEntry && (
                        <div className="p-3 bg-muted rounded-lg text-sm space-y-1">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">原入账记录 #</span>
                            <span className="font-medium">{selectedEntry.id}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">原入账金额</span>
                            <span className="font-medium text-green-600">
                              {formatCurrency(selectedEntry.amount)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">入账日期</span>
                            <span>{formatDate(selectedEntry.entry_date)}</span>
                          </div>
                        </div>
                      )}
                      <FormField
                        control={reversalForm.control}
                        name="reference_id"
                        render={({ field }) => (
                          <Input type="hidden" className="hidden" {...field} />
                        )}
                      />
                      <FormField
                        control={reversalForm.control}
                        name="amount"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>红冲金额</FormLabel>
                            <FormControl>
                              <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                                  ¥
                                </span>
                                <Input
                                  type="number"
                                  step="0.01"
                                  max="-0.01"
                                  placeholder="-0.00"
                                  className="pl-8"
                                  {...field}
                                />
                              </div>
                            </FormControl>
                            <FormDescription>
                              必须为负数，且绝对值不能超过原入账金额
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={reversalForm.control}
                        name="entry_date"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>红冲日期</FormLabel>
                            <FormControl>
                              <div className="relative">
                                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input type="date" className="pl-10" {...field} />
                              </div>
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={reversalForm.control}
                        name="notes"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>红冲原因</FormLabel>
                            <FormControl>
                              <Textarea placeholder="请说明红冲原因..." {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <DialogFooter>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            setIsReversalOpen(false);
                            setSelectedEntry(null);
                          }}
                        >
                          取消
                        </Button>
                        <Button
                          type="submit"
                          variant="destructive"
                          disabled={reversalMutation.isPending}
                        >
                          {reversalMutation.isPending ? '提交中...' : '确认红冲'}
                        </Button>
                      </DialogFooter>
                    </form>
                  </Form>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <PrepaymentTable
            entries={entries}
            isLoading={isEntriesLoading}
            onSelectForReversal={handleSelectForReversal}
          />

          {/* 分页 */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">共 {pagination.total} 条记录</p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  上一页
                </Button>
                <span className="text-sm">
                  {page} / {pagination.total_pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                  disabled={page >= pagination.total_pages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
