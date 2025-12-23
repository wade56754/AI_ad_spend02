/**
 * Transfer Form Component
 *
 * Dialog for creating new transfer requests
 * SoT 对齐: STATE_MACHINE.md v2.6 第12章
 */

'use client';

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
import { Button } from '@/components/ui/button';
import { useCreateTransfer } from '../hooks';

const transferSchema = z.object({
  source_ad_account_id: z.number({ message: '请输入源账户ID' }).int().positive('账户ID必须为正整数'),
  target_ad_account_id: z.number({ message: '请输入目标账户ID' }).int().positive('账户ID必须为正整数'),
  transfer_amount: z.number({ message: '请输入迁移金额' }).positive('迁移金额必须大于0'),
  reason: z.string().max(500, '原因不能超过500字').optional(),
}).refine(data => data.source_ad_account_id !== data.target_ad_account_id, {
  message: '源账户和目标账户不能相同',
  path: ['target_ad_account_id'],
});

type TransferFormValues = z.infer<typeof transferSchema>;

interface TransferFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TransferForm({ open, onOpenChange }: TransferFormProps) {
  const createMutation = useCreateTransfer();

  const form = useForm<TransferFormValues>({
    resolver: zodResolver(transferSchema),
    defaultValues: {
      source_ad_account_id: undefined,
      target_ad_account_id: undefined,
      transfer_amount: undefined,
      reason: '',
    },
  });

  const onSubmit = async (values: TransferFormValues) => {
    try {
      await createMutation.mutateAsync(values);
      form.reset();
      onOpenChange(false);
    } catch (error) {
      console.error('创建迁移申请失败:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>新建迁移申请</DialogTitle>
          <DialogDescription>
            创建死号余额迁移申请，将余额从源账户转移到目标账户
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="source_ad_account_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>源账户ID（死号）</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="输入源账户ID"
                      {...field}
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                      value={field.value ?? ''}
                    />
                  </FormControl>
                  <FormDescription>需要迁移余额的死号账户</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="target_ad_account_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>目标账户ID</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="输入目标账户ID"
                      {...field}
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                      value={field.value ?? ''}
                    />
                  </FormControl>
                  <FormDescription>接收余额的目标账户</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="transfer_amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>迁移金额</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="输入迁移金额"
                      {...field}
                      onChange={(e) => field.onChange(e.target.value ? parseFloat(e.target.value) : undefined)}
                      value={field.value ?? ''}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>迁移原因（可选）</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请输入迁移原因"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? '创建中...' : '创建'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
