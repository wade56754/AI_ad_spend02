"use client";

/**
 * Ad Account Form Component
 *
 * Refactored to use react-hook-form + zod validation
 * SoT: DATA_SCHEMA.md - ad_accounts table
 * SoT: STATE_MACHINE.md - account status enum
 */

import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  CreditCard,
  Users,
  Settings,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  RefreshCw,
  HelpCircle,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPost } from "@/lib/api";

// ============================================================================
// Types
// ============================================================================

interface User {
  id: number;
  username: string;
  nickname: string;
  role: string;
  status: string;
}

interface Project {
  id: number;
  name: string;
  client_name: string;
  status: string;
}

// Platform type
const platforms = ["facebook", "tiktok", "google", "twitter"] as const;
type Platform = (typeof platforms)[number];

// Account status (SoT: STATE_MACHINE.md)
const accountStatuses = ["new", "testing", "active", "suspended", "dead", "archived"] as const;
type AccountStatus = (typeof accountStatuses)[number];

// Account type
const accountTypes = ["personal", "business"] as const;
type AccountType = (typeof accountTypes)[number];

// ============================================================================
// Zod Schema
// ============================================================================

const notificationSettingsSchema = z.object({
  budget_alert: z.boolean().default(true),
  performance_alert: z.boolean().default(true),
  status_change_alert: z.boolean().default(true),
});

const adAccountSchema = z.object({
  name: z.string().min(1, "账户名称不能为空").max(100, "账户名称不能超过100字符"),
  platform: z.enum(platforms, { required_error: "请选择平台" }),
  account_code: z.string().min(1, "账户代码不能为空").max(50, "账户代码不能超过50字符"),
  account_type: z.enum(accountTypes).default("business"),
  currency: z.string().min(1, "请选择货币"),
  timezone: z.string().min(1, "请选择时区"),
  spend_limit: z.number().min(1, "消耗限额必须大于0"),
  daily_budget: z.number().min(1, "日预算必须大于0").optional().nullable(),
  status: z.enum(accountStatuses).default("new"),
  owner_id: z.string().optional().nullable(),
  project_id: z.number().optional().nullable(),
  notes: z.string().max(500, "备注不能超过500字符").optional().nullable(),
  auto_optimization: z.boolean().default(false),
  notification_settings: notificationSettingsSchema.default({
    budget_alert: true,
    performance_alert: true,
    status_change_alert: true,
  }),
});

type AdAccountFormValues = z.infer<typeof adAccountSchema>;

// Extended type for API with optional id
interface AdAccount extends AdAccountFormValues {
  id?: number;
}

// ============================================================================
// Platform Configuration
// ============================================================================

const platformConfigs: Record<
  Platform,
  {
    name: string;
    color: string;
    idPrefix: string;
    currencies: string[];
    features: string[];
  }
> = {
  facebook: {
    name: "Facebook",
    color: "bg-blue-500",
    idPrefix: "act_",
    currencies: ["USD", "EUR", "GBP", "CNY"],
    features: ["受众定向", "重定向", "动态广告", "Messenger广告"],
  },
  tiktok: {
    name: "TikTok",
    color: "bg-black",
    idPrefix: "tt_",
    currencies: ["USD", "EUR", "CNY", "JPY"],
    features: ["短视频广告", "信息流广告", "开屏广告", "品牌挑战"],
  },
  google: {
    name: "Google Ads",
    color: "bg-red-500",
    idPrefix: "ga_",
    currencies: ["USD", "EUR", "GBP", "CNY", "JPY"],
    features: ["搜索广告", "展示广告", "视频广告", "购物广告"],
  },
  twitter: {
    name: "Twitter",
    color: "bg-blue-400",
    idPrefix: "tw_",
    currencies: ["USD", "EUR", "GBP", "CNY"],
    features: ["推文推广", "账户推广", "趋势广告", "视频广告"],
  },
};

const timezones = [
  { value: "Asia/Shanghai", label: "Asia/Shanghai" },
  { value: "Asia/Tokyo", label: "Asia/Tokyo" },
  { value: "UTC", label: "UTC" },
  { value: "America/New_York", label: "America/New_York" },
  { value: "Europe/London", label: "Europe/London" },
];

// ============================================================================
// Props
// ============================================================================

interface AdAccountFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: AdAccount) => Promise<void>;
  editData?: AdAccount;
  mode: "create" | "edit";
}

// ============================================================================
// Component
// ============================================================================

export function AdAccountForm({
  open,
  onClose,
  onSubmit,
  editData,
  mode,
}: AdAccountFormProps) {
  // Form setup with react-hook-form + zod
  const form = useForm<AdAccountFormValues>({
    resolver: zodResolver(adAccountSchema),
    defaultValues: {
      name: "",
      platform: "facebook",
      account_code: "",
      account_type: "business",
      currency: "CNY",
      timezone: "Asia/Shanghai",
      spend_limit: 5000,
      daily_budget: null,
      status: "new",
      owner_id: null,
      project_id: null,
      notes: "",
      auto_optimization: false,
      notification_settings: {
        budget_alert: true,
        performance_alert: true,
        status_change_alert: true,
      },
    },
  });

  // Local state
  const [users, setUsers] = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [validating, setValidating] = useState(false);
  const [accountValid, setAccountValid] = useState<boolean | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Watch platform for dynamic config
  const platform = form.watch("platform");
  const accountCode = form.watch("account_code");
  const dailyBudget = form.watch("daily_budget");
  const platformConfig = platformConfigs[platform];

  // ========== Data Fetching ==========

  const fetchUsers = async () => {
    try {
      const response = await apiGet<{ data: User[] }>("/api/v1/users", {
        role: "pitcher,account_manager",
      });
      if (response.data) {
        setUsers(response.data);
      }
    } catch (error) {
      console.error("获取用户列表失败:", error);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await apiGet<{ data: Project[] }>("/api/v1/projects", {
        status: "active",
      });
      if (response.data) {
        setProjects(response.data);
      }
    } catch (error) {
      console.error("获取项目列表失败:", error);
    }
  };

  // Validate account code
  const validateAccountCode = async () => {
    if (!accountCode || !platform) return;

    setValidating(true);
    setAccountValid(null);

    try {
      const response = await apiPost<{ data?: { valid: boolean } }>(
        `/api/v1/ad-accounts/validate`,
        { platform, account_code: accountCode }
      );
      setAccountValid(response.data?.valid ?? false);
    } catch (error) {
      console.error("验证失败:", error);
      setAccountValid(false);
    } finally {
      setValidating(false);
    }
  };

  // ========== Effects ==========

  // Initialize edit data
  useEffect(() => {
    if (open && editData) {
      form.reset({
        ...editData,
        daily_budget: editData.daily_budget ?? null,
        owner_id: editData.owner_id ?? null,
        project_id: editData.project_id ?? null,
        notes: editData.notes ?? "",
        notification_settings: editData.notification_settings ?? {
          budget_alert: true,
          performance_alert: true,
          status_change_alert: true,
        },
      });
    } else if (open && !editData) {
      form.reset();
    }
  }, [editData, open, form]);

  // Fetch data when dialog opens
  useEffect(() => {
    if (open) {
      fetchUsers();
      fetchProjects();
    }
  }, [open]);

  // Validate account code with debounce
  useEffect(() => {
    if (accountCode && platform) {
      const timer = setTimeout(() => {
        validateAccountCode();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [accountCode, platform]);

  // ========== Handlers ==========

  const handleFormSubmit = async (values: AdAccountFormValues) => {
    if (accountValid === false) {
      toast.error("账户代码无效或已被占用");
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        ...values,
        id: editData?.id,
      });
      toast.success(mode === "create" ? "账户创建成功" : "账户更新成功");
      onClose();
    } catch (error) {
      toast.error("操作失败，请重试");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    form.reset();
    setAccountValid(null);
    setShowAdvanced(false);
    onClose();
  };

  // ========== Render ==========

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            {mode === "create" ? "新建广告账户" : "编辑广告账户"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "创建新的广告账户，请确保信息准确无误"
              : "编辑广告账户信息，修改后请保存"}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-6">
            {/* Platform Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">平台信息</CardTitle>
                <CardDescription>选择广告投放平台</CardDescription>
              </CardHeader>
              <CardContent>
                <FormField
                  control={form.control}
                  name="platform"
                  render={({ field }) => (
                    <FormItem>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {platforms.map((p) => {
                          const config = platformConfigs[p];
                          return (
                            <div
                              key={p}
                              className={`cursor-pointer rounded-lg border-2 p-4 transition-all ${
                                field.value === p
                                  ? "border-blue-500 bg-blue-50"
                                  : "border-gray-200 hover:border-gray-300"
                              }`}
                              onClick={() => field.onChange(p)}
                            >
                              <div className={`w-3 h-3 rounded-full ${config.color} mb-2`} />
                              <div className="font-medium">{config.name}</div>
                              <div className="text-xs text-gray-500 mt-1">
                                ID前缀: {config.idPrefix}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">基本信息</CardTitle>
                <CardDescription>账户的基本配置信息</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          账户名称 <span className="text-red-500">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input placeholder="输入账户名称" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="account_code"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          账户代码 <span className="text-red-500">*</span>
                        </FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input
                              placeholder={`${platformConfig.idPrefix}1234567890`}
                              {...field}
                            />
                            {validating && (
                              <RefreshCw className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
                            )}
                            {accountValid !== null && !validating && (
                              accountValid ? (
                                <CheckCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-green-500" />
                              ) : (
                                <AlertTriangle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-red-500" />
                              )
                            )}
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="account_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>账户类型</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="personal">个人账户</SelectItem>
                            <SelectItem value="business">商业账户</SelectItem>
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
                        <FormLabel>货币</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {platformConfig.currencies.map((currency) => (
                              <SelectItem key={currency} value={currency}>
                                {currency}
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
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {timezones.map((tz) => (
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
                    name="status"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>初始状态</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="new">新建</SelectItem>
                            <SelectItem value="testing">测试中</SelectItem>
                            <SelectItem value="active">活跃</SelectItem>
                            <SelectItem value="suspended">暂停</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="owner_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>负责人</FormLabel>
                        <Select
                          onValueChange={(v) => field.onChange(v === "__none__" ? null : v)}
                          value={field.value ?? "__none__"}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="选择负责人" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="__none__">未分配</SelectItem>
                            {users
                              .filter((user) => user.status === "active")
                              .map((user) => (
                                <SelectItem key={user.id} value={user.id.toString()}>
                                  <div className="flex items-center gap-2">
                                    <Users className="w-4 h-4" />
                                    <span>
                                      {user.nickname} ({user.username})
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

                  <FormField
                    control={form.control}
                    name="project_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>所属项目</FormLabel>
                        <Select
                          onValueChange={(v) =>
                            field.onChange(v === "__none__" ? null : parseInt(v))
                          }
                          value={field.value?.toString() ?? "__none__"}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="选择项目" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="__none__">未分配</SelectItem>
                            {projects
                              .filter((project) => project.status === "active")
                              .map((project) => (
                                <SelectItem key={project.id} value={project.id.toString()}>
                                  {project.name} - {project.client_name}
                                </SelectItem>
                              ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="notes"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>备注</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="输入账户相关备注信息..."
                          rows={3}
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            {/* Budget Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">预算设置</CardTitle>
                <CardDescription>设置账户的消耗限额和预算</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="spend_limit"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          消耗限额 <span className="text-red-500">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            placeholder="输入消耗限额"
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
                    name="daily_budget"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>日预算（可选）</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            placeholder="输入日预算"
                            value={field.value ?? ""}
                            onChange={(e) =>
                              field.onChange(e.target.value ? parseFloat(e.target.value) : null)
                            }
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                {dailyBudget && dailyBudget > 0 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      设置日预算将限制每日消耗，月度消耗限额仍然有效。 当前设置日预算为 ¥
                      {dailyBudget.toLocaleString()}， 月度预计消耗 ¥
                      {(dailyBudget * 30).toLocaleString()}。
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Advanced Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  高级设置
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                  >
                    {showAdvanced ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    {showAdvanced ? "隐藏" : "显示"}
                  </Button>
                </CardTitle>
              </CardHeader>
              {showAdvanced && (
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="auto_optimization"
                    render={({ field }) => (
                      <FormItem className="flex items-center space-x-2">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <FormLabel className="!mt-0">启用自动优化</FormLabel>
                      </FormItem>
                    )}
                  />

                  <div className="space-y-3">
                    <FormLabel>通知设置</FormLabel>
                    <div className="space-y-2">
                      <FormField
                        control={form.control}
                        name="notification_settings.budget_alert"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2">
                            <FormControl>
                              <Checkbox
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                            <FormLabel className="!mt-0">预算告警通知</FormLabel>
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="notification_settings.performance_alert"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2">
                            <FormControl>
                              <Checkbox
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                            <FormLabel className="!mt-0">性能异常通知</FormLabel>
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="notification_settings.status_change_alert"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2">
                            <FormControl>
                              <Checkbox
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                            <FormLabel className="!mt-0">状态变更通知</FormLabel>
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>

            {/* Platform Features */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <HelpCircle className="w-5 h-5" />
                  {platformConfig.name} 平台特性
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {platformConfig.features.map((feature, index) => (
                    <Badge key={index} variant="outline" className="justify-center">
                      {feature}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                取消
              </Button>
              <Button type="submit" disabled={isSubmitting || accountValid === false}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {mode === "create" ? "创建中..." : "保存中..."}
                  </>
                ) : (
                  <>{mode === "create" ? "创建账户" : "保存修改"}</>
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
