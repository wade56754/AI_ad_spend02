/**
 * BasicSettings - 基础配置组件
 *
 * TASK-FE-SET-002: 基础配置表单
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
 *
 * 功能:
 * - 系统名称配置
 * - 日期格式配置
 * - 语言/时区配置
 * - 保存成功显示 toast
 */

'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Loader2, Save, Settings2, Globe, Calendar, Type } from 'lucide-react';
import { toast } from 'sonner';

// === 类型定义 ===

const basicSettingsSchema = z.object({
  systemName: z.string().min(1, '系统名称不能为空').max(50, '系统名称最多50个字符'),
  dateFormat: z.enum(['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY年MM月DD日']),
  timezone: z.string().min(1, '请选择时区'),
  language: z.enum(['zh-CN', 'en-US']),
  currency: z.enum(['CNY', 'USD']),
  defaultPageSize: z.number().min(10).max(100),
});

type BasicSettingsFormValues = z.infer<typeof basicSettingsSchema>;

export interface BasicSettingsProps {
  /** 初始值 */
  initialValues?: Partial<BasicSettingsFormValues>;
  /** 变更回调 */
  onChange?: () => void;
  /** 保存回调 */
  onSave?: (values: BasicSettingsFormValues) => Promise<void>;
}

// === 常量配置 ===

const DATE_FORMATS = [
  { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD (2025-01-06)' },
  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (06/01/2025)' },
  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (01/06/2025)' },
  { value: 'YYYY年MM月DD日', label: 'YYYY年MM月DD日 (2025年01月06日)' },
];

const TIMEZONES = [
  { value: 'Asia/Shanghai', label: '北京时间 (UTC+8)' },
  { value: 'Asia/Hong_Kong', label: '香港时间 (UTC+8)' },
  { value: 'Asia/Tokyo', label: '东京时间 (UTC+9)' },
  { value: 'America/New_York', label: '纽约时间 (UTC-5)' },
  { value: 'America/Los_Angeles', label: '洛杉矶时间 (UTC-8)' },
  { value: 'Europe/London', label: '伦敦时间 (UTC+0)' },
];

const LANGUAGES = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en-US', label: 'English (US)' },
];

const CURRENCIES = [
  { value: 'CNY', label: '人民币 (¥)' },
  { value: 'USD', label: '美元 ($)' },
];

const PAGE_SIZES = [10, 20, 50, 100];

// === 默认值 ===

const DEFAULT_VALUES: BasicSettingsFormValues = {
  systemName: 'AI广告代投管理系统',
  dateFormat: 'YYYY-MM-DD',
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  currency: 'CNY',
  defaultPageSize: 20,
};

// === 主组件 ===

export function BasicSettings({
  initialValues,
  onChange,
  onSave,
}: BasicSettingsProps) {
  const [isSaving, setIsSaving] = useState(false);

  const form = useForm<BasicSettingsFormValues>({
    resolver: zodResolver(basicSettingsSchema),
    defaultValues: {
      ...DEFAULT_VALUES,
      ...initialValues,
    },
  });

  // 监听表单变更
  const handleFieldChange = () => {
    onChange?.();
  };

  // 提交表单
  const handleSubmit = async (values: BasicSettingsFormValues) => {
    setIsSaving(true);
    try {
      if (onSave) {
        await onSave(values);
      } else {
        // 模拟保存
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      toast.success('基础配置保存成功');
    } catch (error) {
      toast.error(`保存失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        {/* 系统信息 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Settings2 className="h-4 w-4" />
              系统信息
            </CardTitle>
            <CardDescription>配置系统基本信息</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="systemName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>系统名称</FormLabel>
                  <FormControl>
                    <div className="flex items-center gap-2">
                      <Type className="h-4 w-4 text-muted-foreground" />
                      <Input
                        {...field}
                        placeholder="请输入系统名称"
                        onChange={(e) => {
                          field.onChange(e);
                          handleFieldChange();
                        }}
                      />
                    </div>
                  </FormControl>
                  <FormDescription>显示在浏览器标题和登录页面</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* 地区与语言 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Globe className="h-4 w-4" />
              地区与语言
            </CardTitle>
            <CardDescription>配置系统语言和地区设置</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="language"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>系统语言</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                        handleFieldChange();
                      }}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择语言" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {LANGUAGES.map((lang) => (
                          <SelectItem key={lang.value} value={lang.value}>
                            {lang.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="timezone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>时区</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                        handleFieldChange();
                      }}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择时区" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {TIMEZONES.map((tz) => (
                          <SelectItem key={tz.value} value={tz.value}>
                            {tz.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="currency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>默认货币</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                        handleFieldChange();
                      }}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择货币" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {CURRENCIES.map((curr) => (
                          <SelectItem key={curr.value} value={curr.value}>
                            {curr.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        {/* 显示格式 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Calendar className="h-4 w-4" />
              显示格式
            </CardTitle>
            <CardDescription>配置日期和分页显示格式</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="dateFormat"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>日期格式</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={(value) => {
                        field.onChange(value);
                        handleFieldChange();
                      }}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择日期格式" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {DATE_FORMATS.map((fmt) => (
                          <SelectItem key={fmt.value} value={fmt.value}>
                            {fmt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>在整个系统中使用的日期显示格式</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="defaultPageSize"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>默认每页条数</FormLabel>
                    <Select
                      value={String(field.value)}
                      onValueChange={(value) => {
                        field.onChange(Number(value));
                        handleFieldChange();
                      }}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择每页条数" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {PAGE_SIZES.map((size) => (
                          <SelectItem key={size} value={String(size)}>
                            {size} 条/页
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>列表页面默认显示的数据条数</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        {/* 保存按钮 */}
        <div className="flex justify-end">
          <Button type="submit" disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                保存基础配置
              </>
            )}
          </Button>
        </div>
      </form>
    </Form>
  );
}

export default BasicSettings;
