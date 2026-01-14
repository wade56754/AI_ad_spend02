/**
 * AdjustmentForm - 资金调整表单
 *
 * 用于财务人员进行金额修正和调整
 *
 * SoT References:
 * - BR-FIN.md v1.1 (财务调整规则)
 * - LEDGER_SOT.md v1.1 (账本规则 - ADJUSTMENT 类型)
 * - MASTER.md v4.9 §2.4 (权限: admin, finance)
 *
 * 调整类型说明:
 * - 金额修正: 修正错误的金额记录
 * - 汇率调整: 汇率变动导致的金额调整
 * - 退款调整: 部分退款或退款差额
 * - 手续费调整: 手续费差额
 * - 其他调整: 其他类型的调整
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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import {
  Settings2,
  Loader2,
  Plus,
  Minus,
  AlertTriangle,
} from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useCreateTransaction } from '../hooks/useLedgerMutations';
import { useProjects } from '@/features/projects/hooks/useProjects';

// === 调整类别定义 ===
const ADJUSTMENT_CATEGORIES = [
  { value: 'amount_correction', label: '金额修正', description: '修正错误的金额记录' },
  { value: 'exchange_rate', label: '汇率调整', description: '汇率变动导致的调整' },
  { value: 'refund_diff', label: '退款差额', description: '退款金额差异调整' },
  { value: 'fee_diff', label: '手续费差额', description: '手续费差额调整' },
  { value: 'other', label: '其他调整', description: '其他类型的调整' },
] as const;

// === 表单验证 Schema ===
const adjustmentFormSchema = z.object({
  direction: z.enum(['increase', 'decrease'], {
    required_error: '请选择调整方向',
  }),
  amount: z
    .string()
    .min(1, '请输入调整金额')
    .refine((val) => !isNaN(Number(val)) && Number(val) > 0, {
      message: '金额必须大于 0',
    }),
  currency: z.string().default('USD'),
  category: z.enum(['amount_correction', 'exchange_rate', 'refund_diff', 'fee_diff', 'other'], {
    required_error: '请选择调整类别',
  }),
  project_id: z.string().optional(),
  reference_id: z.string().optional(),
  reason: z.string().min(10, '请详细说明调整原因（至少 10 字）').max(500, '说明不能超过 500 字'),
});

type AdjustmentFormValues = z.infer<typeof adjustmentFormSchema>;

// === Props 定义 ===
interface AdjustmentFormProps {
  /** 创建成功后的回调 */
  onSuccess?: () => void;
  /** 触发按钮的变体 */
  triggerVariant?: 'default' | 'outline' | 'ghost';
}

export function AdjustmentForm({
  onSuccess,
  triggerVariant = 'outline',
}: AdjustmentFormProps) {
  const [open, setOpen] = useState(false);
  const createTransaction = useCreateTransaction();

  // 获取项目列表
  const { data: projectsData } = useProjects({ page: 1, page_size: 100 });
  const projects = projectsData?.items ?? [];

  const form = useForm<AdjustmentFormValues>({
    resolver: zodResolver(adjustmentFormSchema),
    defaultValues: {
      direction: undefined,
      amount: '',
      currency: 'USD',
      category: undefined,
      project_id: '',
      reference_id: '',
      reason: '',
    },
  });

  const watchDirection = form.watch('direction');

  const onSubmit = async (values: AdjustmentFormValues) => {
    try {
      // 构建描述信息
      const categoryLabel = ADJUSTMENT_CATEGORIES.find(c => c.value === values.category)?.label ?? values.category;
      const directionLabel = values.direction === 'increase' ? '增加' : '减少';
      const description = `[${categoryLabel}] ${directionLabel} ${values.amount} ${values.currency} - ${values.reason}`;

      await createTransaction.mutateAsync({
        transaction_type: 'ADJUSTMENT',
        amount: Number(values.amount),
        currency: values.currency,
        project_id: values.project_id || undefined,
        reference_id: values.reference_id || undefined,
        description,
        metadata: {
          adjustment_category: values.category,
          adjustment_direction: values.direction,
          original_reason: values.reason,
        },
      });

      toast.success('调整创建成功', {
        description: `已成功创建${directionLabel}调整，金额 ${values.amount} ${values.currency}`,
      });

      form.reset();
      setOpen(false);
      onSuccess?.();
    } catch (error) {
      toast.error('调整失败', {
        description: error instanceof Error ? error.message : '创建调整失败，请重试',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant={triggerVariant} size="sm">
          <Settings2 className="mr-2 h-4 w-4" />
          资金调整
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5 text-amber-600" />
            资金调整
          </DialogTitle>
          <DialogDescription>
            对账户余额进行调整修正。调整后将生成不可逆的账本记录，请谨慎操作。
          </DialogDescription>
        </DialogHeader>

        {/* 警告提示 */}
        <Alert variant="destructive" className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-800">重要提示</AlertTitle>
          <AlertDescription className="text-amber-700">
            资金调整将直接影响账户余额，一经创建无法撤销。请仔细核对金额和原因。
          </AlertDescription>
        </Alert>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* 调整方向 */}
            <FormField
              control={form.control}
              name="direction"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>调整方向 *</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={field.onChange}
                      value={field.value}
                      className="flex gap-4"
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="increase" id="increase" />
                        <Label
                          htmlFor="increase"
                          className="flex items-center gap-1 text-emerald-600 cursor-pointer"
                        >
                          <Plus className="h-4 w-4" />
                          增加余额
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="decrease" id="decrease" />
                        <Label
                          htmlFor="decrease"
                          className="flex items-center gap-1 text-red-600 cursor-pointer"
                        >
                          <Minus className="h-4 w-4" />
                          减少余额
                        </Label>
                      </div>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 调整类别 */}
            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>调整类别 *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择调整类别" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {ADJUSTMENT_CATEGORIES.map((cat) => (
                        <SelectItem key={cat.value} value={cat.value}>
                          <div className="flex flex-col">
                            <span>{cat.label}</span>
                            <span className="text-xs text-muted-foreground">
                              {cat.description}
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
                    <FormLabel>调整金额 *</FormLabel>
                    <FormControl>
                      <div className="relative">
                        {watchDirection === 'increase' ? (
                          <Plus className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-500" />
                        ) : watchDirection === 'decrease' ? (
                          <Minus className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-red-500" />
                        ) : (
                          <Settings2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        )}
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
                  <FormLabel>关联项目</FormLabel>
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
                    如果调整针对特定项目，请选择对应项目
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
                  <FormLabel>关联单号</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="关联的业务单号（可选）" />
                  </FormControl>
                  <FormDescription>
                    如充值单号、日报ID等需要修正的业务单据
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 调整原因 */}
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>调整原因 *</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="请详细说明调整原因，包括：&#10;1. 原因说明&#10;2. 相关依据（如有）&#10;3. 审批人信息（如有）"
                      className="resize-none"
                      rows={4}
                    />
                  </FormControl>
                  <FormDescription>
                    详细的调整原因有助于后续审计和查询（至少 10 字）
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
              <Button
                type="submit"
                disabled={createTransaction.isPending}
                className={
                  watchDirection === 'increase'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : watchDirection === 'decrease'
                    ? 'bg-red-600 hover:bg-red-700'
                    : ''
                }
              >
                {createTransaction.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    处理中...
                  </>
                ) : (
                  <>
                    {watchDirection === 'increase' ? (
                      <Plus className="mr-2 h-4 w-4" />
                    ) : watchDirection === 'decrease' ? (
                      <Minus className="mr-2 h-4 w-4" />
                    ) : (
                      <Settings2 className="mr-2 h-4 w-4" />
                    )}
                    确认调整
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

export default AdjustmentForm;
