/**
 * Channel Form Component
 *
 * Create/Edit channel form with validation
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateChannel, useUpdateChannel } from '../hooks';
import type { Channel, ChannelCreateInput, ServiceFeeType } from '../types';

const channelSchema = z.object({
  name: z.string().min(1, '渠道名称不能为空').max(100, '渠道名称不能超过100字符'),
  channel_code: z.string().max(50, '渠道代码不能超过50字符').optional(),
  service_fee_type: z.enum(['percent', 'fixed'] as const),
  service_fee_value: z
    .number({ invalid_type_error: '请输入有效数字' })
    .min(0, '服务费不能为负数'),
});

type ChannelFormValues = z.infer<typeof channelSchema>;

interface ChannelFormProps {
  channel?: Channel | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ChannelForm({ channel, open, onOpenChange }: ChannelFormProps) {
  const isEdit = !!channel;

  const createMutation = useCreateChannel({
    onSuccess: () => {
      onOpenChange(false);
    },
  });

  const updateMutation = useUpdateChannel({
    onSuccess: () => {
      onOpenChange(false);
    },
  });

  const form = useForm<ChannelFormValues>({
    resolver: zodResolver(channelSchema),
    defaultValues: {
      name: '',
      channel_code: '',
      service_fee_type: 'percent',
      service_fee_value: 0,
    },
  });

  useEffect(() => {
    if (channel) {
      form.reset({
        name: channel.name,
        channel_code: channel.channel_code || '',
        service_fee_type: channel.service_fee_type as ServiceFeeType,
        service_fee_value: channel.service_fee_value,
      });
    } else {
      form.reset({
        name: '',
        channel_code: '',
        service_fee_type: 'percent',
        service_fee_value: 0,
      });
    }
  }, [channel, form]);

  const onSubmit = (values: ChannelFormValues) => {
    const input: ChannelCreateInput = {
      name: values.name,
      channel_code: values.channel_code || undefined,
      service_fee_type: values.service_fee_type,
      service_fee_value: values.service_fee_value,
    };

    if (isEdit && channel) {
      updateMutation.mutate({ id: channel.id, input });
    } else {
      createMutation.mutate(input);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑渠道' : '新建渠道'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>渠道名称 *</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入渠道名称" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="channel_code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>渠道代码</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入渠道代码（可选）" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="service_fee_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>服务费类型 *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择服务费类型" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="percent">百分比</SelectItem>
                      <SelectItem value="fixed">固定金额</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="service_fee_value"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    服务费{' '}
                    {form.watch('service_fee_type') === 'percent' ? '(%)' : '(¥)'} *
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="请输入服务费"
                      {...field}
                      onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isPending}
              >
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '保存中...' : '保存'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
