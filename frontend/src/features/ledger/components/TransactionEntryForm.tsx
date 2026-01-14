/**
 * TransactionEntryForm - 交易录入表单
 *
 * 用于财务人员手工录入交易记录
 *
 * SoT References:
 * - BR-FIN.md v1.1 (财务流程规则)
 * - LEDGER_SOT.md v1.1 (账本规则)
 * - MASTER.md v4.9 §2.4 (权限: admin, finance)
 *
 * 支持的交易类型:
 * - TOPUP: 充值
 * - SPEND: 消耗
 * - REFUND: 退款
 * - FEE: 手续费
 * - ADJUSTMENT: 调整
 * - TRANSFER: 转账
 *
 * @module features/ledger/components
 */

'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { Plus, Loader2, DollarSign, FileText, Building2 } from 'lucide-react';
import { useCreateTransaction } from '../hooks/useLedgerMutations';
import { useProjects } from '@/features/projects/hooks/useProjects';

// === 交易类型定义 ===
const TRANSACTION_TYPES = [
  { value: 'TOPUP', label: '充值', description: '账户充值', icon: '💰' },
  { value: 'SPEND', label: '消耗', description: '广告消耗', icon: '📊' },
  { value: 'REFUND', label: '退款', description: '退款入账', icon: '↩️' },
  { value: 'FEE', label: '手续费', description: '渠道手续费', icon: '💳' },
  { value: 'ADJUSTMENT', label: '调整', description: '金额修正', icon: '⚙️' },
  { value: 'TRANSFER', label: '转账', description: '项目间转账', icon: '🔄' },
] as const;

// === 表单验证 Schema ===
const transactionFormSchema = z.object({
  transaction_type: z.enum(['TOPUP', 'SPEND', 'REFUND', 'FEE', 'ADJUSTMENT', 'TRANSFER'], {
    required_error: '请选择交易类型',
  }),
  amount: z
    .string()
    .min(1, '请输入金额')
    .refine((val) => !isNaN(Number(val)) && Number(val) > 0, {
      message: '金额必须大于 0',
    }),
  currency: z.string().default('USD'),
  project_id: z.string().optional(),
  account_id: z.string().optional(),
  reference_id: z.string().optional(),
  description: z.string().min(1, '请输入交易说明').max(500, '说明不能超过 500 字'),
});

type TransactionFormValues = z.infer<typeof transactionFormSchema>;

// === Props 定义 ===
interface TransactionEntryFormProps {
  /** 创建成功后的回调 */
  onSuccess?: () => void;
  /** 触发按钮的变体 */
  triggerVariant?: 'default' | 'outline' | 'ghost';
  /** 触发按钮大小 */
  triggerSize?: 'default' | 'sm' | 'lg';
}

export function TransactionEntryForm({
  onSuccess,
  triggerVariant = 'default',
  triggerSize = 'default',
}: TransactionEntryFormProps) {
  const [open, setOpen] = useState(false);
  const createTransaction = useCreateTransaction();

  // 获取项目列表用于选择
  const { data: projectsData } = useProjects({ page: 1, page_size: 100 });
  const projects = projectsData?.items ?? [];

  const form = useForm<TransactionFormValues>({
    resolver: zodResolver(transactionFormSchema),
    defaultValues: {
      transaction_type: undefined,
      amount: '',
      currency: 'USD',
      project_id: '',
      account_id: '',
      reference_id: '',
      description: '',
    },
  });

  const selectedType = form.watch('transaction_type');

  const onSubmit = async (values: TransactionFormValues) => {
    try {
      await createTransaction.mutateAsync({
        transaction_type: values.transaction_type,
        amount: Number(values.amount),
        currency: values.currency,
        project_id: values.project_id || undefined,
        account_id: values.account_id || undefined,
        reference_id: values.reference_id || undefined,
        description: values.description,
      });

      toast.success('交易创建成功', {
        description: `已成功创建 ${TRANSACTION_TYPES.find(t => t.value === values.transaction_type)?.label} 交易`,
      });

      form.reset();
      setOpen(false);
      onSuccess?.();
    } catch (error) {
      toast.error('创建失败', {
        description: error instanceof Error ? error.message : '创建交易失败，请重试',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant={triggerVariant} size={triggerSize}>
          <Plus className="mr-2 h-4 w-4" />
          新建交易
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-emerald-600" />
            新建交易记录
          </DialogTitle>
          <DialogDescription>
            手工录入财务交易记录。请确保信息准确，提交后将无法修改。
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* 交易类型选择 */}
            <FormField
              control={form.control}
              name="transaction_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>交易类型 *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择交易类型" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {TRANSACTION_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          <div className="flex items-center gap-2">
                            <span>{type.icon}</span>
                            <span>{type.label}</span>
                            <span className="text-muted-foreground text-xs">
                              - {type.description}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 金额和货币 */}
            <div className="grid grid-cols-3 gap-4">
              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem className="col-span-2">
                    <FormLabel>金额 *</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          {...field}
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="0.00"
                          className="pl-9"
                        />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="currency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>货币</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="CNY">CNY</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* 关联项目 */}
            <FormField
              control={form.control}
              name="project_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    <Building2 className="h-4 w-4" />
                    关联项目
                  </FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择关联项目（可选）" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="">不关联项目</SelectItem>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={String(project.id)}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    {selectedType === 'TRANSFER'
                      ? '选择转出项目'
                      : '选择交易关联的项目'}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 关联单号 */}
            <FormField
              control={form.control}
              name="reference_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    关联单号
                  </FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="输入关联的业务单号（可选）" />
                  </FormControl>
                  <FormDescription>
                    如充值单号、日报ID等关联业务单据
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 交易说明 */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>交易说明 *</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="请详细描述交易原因和备注..."
                      className="resize-none"
                      rows={3}
                    />
                  </FormControl>
                  <FormDescription>
                    请详细说明交易原因，便于后续审计和查询
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={createTransaction.isPending}
              >
                取消
              </Button>
              <Button type="submit" disabled={createTransaction.isPending}>
                {createTransaction.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    创建中...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    创建交易
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

export default TransactionEntryForm;
