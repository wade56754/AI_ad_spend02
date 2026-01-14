/**
 * ReversalDialog - 红冲对话框
 *
 * 用于冲正错误的交易记录（红冲）
 *
 * SoT References:
 * - BR-FIN.md v1.1 §BR-FIN-007 (红冲规则)
 * - LEDGER_SOT.md v1.1 (账本不可变规则)
 * - MASTER.md v4.9 §2.4 (权限: admin, finance)
 *
 * 红冲规则:
 * 1. 红冲不删除原交易，而是创建一笔反向交易
 * 2. 红冲后原交易和冲正交易都会保留
 * 3. 红冲金额必须与原交易相同
 * 4. 需要填写红冲原因
 *
 * @module features/ledger/components
 */

'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import {
  RotateCcw,
  Loader2,
  AlertTriangle,
  ArrowRight,
  Receipt,
} from 'lucide-react';
import { useCreateReversal } from '../hooks/useLedgerMutations';
import { formatCurrency, formatDateTime } from '@/lib/format';

// === 表单验证 Schema ===
const reversalFormSchema = z.object({
  reason: z
    .string()
    .min(10, '请详细说明红冲原因（至少 10 字）')
    .max(500, '原因不能超过 500 字'),
});

type ReversalFormValues = z.infer<typeof reversalFormSchema>;

// === 交易信息类型 ===
interface TransactionInfo {
  id: string;
  transaction_number: string;
  transaction_type: string;
  amount: number;
  currency: string;
  description?: string;
  created_at: string;
}

// === Props 定义 ===
interface ReversalDialogProps {
  /** 要红冲的交易信息 */
  transaction: TransactionInfo;
  /** 红冲成功后的回调 */
  onSuccess?: () => void;
  /** 触发按钮的变体 */
  triggerVariant?: 'default' | 'outline' | 'ghost' | 'destructive';
  /** 是否显示触发按钮文字 */
  showTriggerText?: boolean;
}

// === 交易类型标签 ===
const TRANSACTION_TYPE_LABELS: Record<string, string> = {
  TOPUP: '充值',
  SPEND: '消耗',
  REFUND: '退款',
  FEE: '手续费',
  ADJUSTMENT: '调整',
  TRANSFER: '转账',
};

export function ReversalDialog({
  transaction,
  onSuccess,
  triggerVariant = 'ghost',
  showTriggerText = false,
}: ReversalDialogProps) {
  const [open, setOpen] = useState(false);
  const createReversal = useCreateReversal();

  const form = useForm<ReversalFormValues>({
    resolver: zodResolver(reversalFormSchema),
    defaultValues: {
      reason: '',
    },
  });

  const onSubmit = async (values: ReversalFormValues) => {
    try {
      await createReversal.mutateAsync({
        transactionId: transaction.id,
        reason: values.reason,
      });

      toast.success('红冲成功', {
        description: `交易 ${transaction.transaction_number} 已成功冲正`,
      });

      form.reset();
      setOpen(false);
      onSuccess?.();
    } catch (error) {
      toast.error('红冲失败', {
        description: error instanceof Error ? error.message : '红冲失败，请重试',
      });
    }
  };

  const typeLabel = TRANSACTION_TYPE_LABELS[transaction.transaction_type] ?? transaction.transaction_type;

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant={triggerVariant}
          size="sm"
          className="text-red-600 hover:text-red-700 hover:bg-red-50"
        >
          <RotateCcw className="h-4 w-4" />
          {showTriggerText && <span className="ml-2">红冲</span>}
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent className="sm:max-w-[500px]">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2 text-red-600">
            <RotateCcw className="h-5 w-5" />
            红冲交易
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p>
                红冲将创建一笔等额反向交易来冲销原交易。原交易记录将保留，
                但账户余额会被调整。此操作不可逆。
              </p>

              {/* 交易信息卡片 */}
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Receipt className="h-4 w-4 text-red-600" />
                    <span className="font-medium text-red-900">
                      {transaction.transaction_number}
                    </span>
                  </div>
                  <Badge variant="outline" className="text-red-600 border-red-200">
                    {typeLabel}
                  </Badge>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-red-700">金额</span>
                  <span className="font-bold text-red-900">
                    {formatCurrency(transaction.amount)} {transaction.currency}
                  </span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-red-700">创建时间</span>
                  <span className="text-red-900">
                    {formatDateTime(transaction.created_at)}
                  </span>
                </div>

                {transaction.description && (
                  <div className="text-sm">
                    <span className="text-red-700">说明: </span>
                    <span className="text-red-900">{transaction.description}</span>
                  </div>
                )}

                {/* 红冲示意 */}
                <div className="flex items-center justify-center gap-2 pt-2 border-t border-red-200">
                  <span className="text-red-700 text-sm">原交易</span>
                  <ArrowRight className="h-4 w-4 text-red-400" />
                  <span className="text-red-900 font-medium text-sm">
                    创建反向交易 (-{formatCurrency(transaction.amount)})
                  </span>
                </div>
              </div>

              {/* 警告提示 */}
              <div className="flex items-start gap-2 text-amber-700 bg-amber-50 rounded-lg p-3">
                <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span className="text-sm">
                  红冲后无法撤销，请确认此操作。建议先核实交易详情。
                </span>
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 红冲原因 */}
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-foreground">红冲原因 *</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="请详细说明红冲原因..."
                      className="resize-none"
                      rows={3}
                    />
                  </FormControl>
                  <FormDescription>
                    详细的红冲原因便于后续审计（至少 10 字）
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <AlertDialogFooter>
              <AlertDialogCancel disabled={createReversal.isPending}>
                取消
              </AlertDialogCancel>
              <AlertDialogAction
                type="submit"
                disabled={createReversal.isPending}
                className="bg-red-600 hover:bg-red-700"
                onClick={(e) => {
                  e.preventDefault();
                  form.handleSubmit(onSubmit)();
                }}
              >
                {createReversal.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    处理中...
                  </>
                ) : (
                  <>
                    <RotateCcw className="mr-2 h-4 w-4" />
                    确认红冲
                  </>
                )}
              </AlertDialogAction>
            </AlertDialogFooter>
          </form>
        </Form>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default ReversalDialog;
