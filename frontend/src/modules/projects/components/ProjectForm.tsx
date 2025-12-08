/**
 * Project Form Component
 *
 * Create/Edit project form with validation
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
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateProject, useUpdateProject } from '../hooks';
import type { Project, ProjectCreateInput } from '../types';

const projectSchema = z.object({
  name: z.string().min(1, '项目名称不能为空').max(200),
  client_name: z.string().min(1, '客户名称不能为空').max(200),
  client_company: z.string().min(1, '客户公司不能为空').max(200),
  description: z.string().max(1000).optional(),
  budget: z.number().min(0, '预算不能为负').optional(),
  currency: z.string().default('USD'),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

interface ProjectFormProps {
  project?: Project | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProjectForm({ project, open, onOpenChange }: ProjectFormProps) {
  const isEdit = !!project;

  const createMutation = useCreateProject({
    onSuccess: () => onOpenChange(false),
  });

  const updateMutation = useUpdateProject({
    onSuccess: () => onOpenChange(false),
  });

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: '',
      client_name: '',
      client_company: '',
      description: '',
      budget: 0,
      currency: 'USD',
    },
  });

  useEffect(() => {
    if (project) {
      form.reset({
        name: project.name,
        client_name: project.client_name,
        client_company: project.client_company,
        description: project.description || '',
        budget: project.budget,
        currency: project.currency,
        start_date: project.start_date || '',
        end_date: project.end_date || '',
      });
    } else {
      form.reset({
        name: '',
        client_name: '',
        client_company: '',
        description: '',
        budget: 0,
        currency: 'USD',
      });
    }
  }, [project, form]);

  const onSubmit = (values: ProjectFormValues) => {
    const input: ProjectCreateInput = {
      name: values.name,
      client_name: values.client_name,
      client_company: values.client_company,
      description: values.description,
      budget: values.budget,
      currency: values.currency,
      start_date: values.start_date || undefined,
      end_date: values.end_date || undefined,
    };

    if (isEdit && project) {
      updateMutation.mutate({ id: project.id, input });
    } else {
      createMutation.mutate(input);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑项目' : '新建项目'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>项目名称 *</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入项目名称" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="client_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>客户联系人 *</FormLabel>
                    <FormControl>
                      <Input placeholder="联系人姓名" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="client_company"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>客户公司 *</FormLabel>
                    <FormControl>
                      <Input placeholder="公司名称" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>项目描述</FormLabel>
                  <FormControl>
                    <Textarea placeholder="项目描述（可选）" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="budget"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>预算</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        {...field}
                        onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                      />
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
                        <SelectItem value="EUR">EUR</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>开始日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="end_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>结束日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

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
