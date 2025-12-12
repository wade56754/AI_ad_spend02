/**
 * 表单组件标准模式 - AI 广告代投系统
 * Version: 1.0
 * SoT Reference: API_SOT.md v9.0
 *
 * 本文件展示表单组件的标准写法，供 AI 代码生成参考。
 *
 * 关键模式：
 * 1. React Hook Form + Zod 验证
 * 2. shadcn/ui 表单组件
 * 3. 受控组件与 Dialog 结合
 * 4. 错误处理与提示
 * 5. 加载状态管理
 */

'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { CalendarIcon, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

// === Zod Schema 定义 ===

const exampleFormSchema = z.object({
  // 必填字段
  name: z
    .string()
    .min(1, '名称不能为空')
    .max(100, '名称不能超过100个字符'),

  amount: z
    .number({ invalid_type_error: '请输入有效的金额' })
    .min(0, '金额不能为负数')
    .max(999999999.99, '金额超出范围'),

  report_date: z
    .date({ required_error: '请选择日期' })
    .refine(
      (date) => date <= new Date(),
      '日期不能是未来日期'
    ),

  // 可选字段
  description: z
    .string()
    .max(500, '描述不能超过500个字符')
    .optional(),

  category: z.enum(['type_a', 'type_b', 'type_c'], {
    errorMap: () => ({ message: '请选择类别' }),
  }),

  // 关联字段
  account_id: z
    .number({ required_error: '请选择账户' })
    .positive('请选择有效的账户'),
});

type ExampleFormValues = z.infer<typeof exampleFormSchema>;

// === 组件 Props ===

interface ExampleFormProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  // 编辑模式时传入初始数据
  initialData?: Partial<ExampleFormValues>;
  mode?: 'create' | 'edit';
}

// === 表单组件 ===

export function ExampleForm({
  open,
  onClose,
  onSuccess,
  initialData,
  mode = 'create',
}: ExampleFormProps) {
  const { toast } = useToast();

  // === 表单初始化 ===

  const form = useForm<ExampleFormValues>({
    resolver: zodResolver(exampleFormSchema),
    defaultValues: {
      name: '',
      amount: 0,
      description: '',
      category: undefined,
      account_id: undefined,
      report_date: new Date(),
      ...initialData,
    },
  });

  const { isSubmitting } = form.formState;

  // === 编辑模式：重置表单数据 ===

  useEffect(() => {
    if (open && initialData) {
      form.reset({
        ...form.getValues(),
        ...initialData,
      });
    }
  }, [open, initialData, form]);

  // === 提交处理 ===

  const onSubmit = async (values: ExampleFormValues) => {
    try {
      // 调用 API
      // if (mode === 'create') {
      //   await exampleApi.create(values);
      // } else {
      //   await exampleApi.update(initialData?.id, values);
      // }

      console.log('Form values:', values);

      toast({
        title: mode === 'create' ? '创建成功' : '更新成功',
        description: `${values.name} 已${mode === 'create' ? '创建' : '更新'}`,
      });

      onSuccess();
      onClose();
      form.reset();
    } catch (error) {
      const message = error instanceof Error ? error.message : '操作失败';
      toast({
        title: '操作失败',
        description: message,
        variant: 'destructive',
      });
    }
  };

  // === 关闭处理 ===

  const handleClose = () => {
    if (!isSubmitting) {
      form.reset();
      onClose();
    }
  };

  // === 渲染 ===

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? '新建' : '编辑'}示例
          </DialogTitle>
          <DialogDescription>
            填写以下信息{mode === 'create' ? '创建' : '更新'}示例数据
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 名称字段 */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>名称 *</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入名称" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 金额字段 */}
            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>金额 *</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      {...field}
                      onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormDescription>单位：元</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 日期字段 */}
            <FormField
              control={form.control}
              name="report_date"
              render={({ field }) => (
                <FormItem className="flex flex-col">
                  <FormLabel>日期 *</FormLabel>
                  <Popover>
                    <PopoverTrigger asChild>
                      <FormControl>
                        <Button
                          variant="outline"
                          className={cn(
                            'w-full pl-3 text-left font-normal',
                            !field.value && 'text-muted-foreground'
                          )}
                        >
                          {field.value ? (
                            format(field.value, 'yyyy-MM-dd')
                          ) : (
                            <span>选择日期</span>
                          )}
                          <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                        </Button>
                      </FormControl>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={field.value}
                        onSelect={field.onChange}
                        disabled={(date) => date > new Date()}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 类别选择 */}
            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>类别 *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择类别" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="type_a">类型 A</SelectItem>
                      <SelectItem value="type_b">类型 B</SelectItem>
                      <SelectItem value="type_c">类型 C</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 描述字段（可选） */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>描述</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请输入描述（可选）"
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>最多500个字符</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 表单按钮 */}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isSubmitting}
              >
                取消
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {mode === 'create' ? '创建' : '保存'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

// === 导出 ===

export default ExampleForm;
