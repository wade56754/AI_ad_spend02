"use client";

import React, { useEffect } from "react";
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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Users,
  CreditCard,
  Activity,
  Settings,
  DollarSign,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, isApiError } from "@/lib/api";

// 类型定义 - 对齐 init_schema.sql §5.1
interface AdAccount {
  id: number;
  name: string;
  platform: string;
  status: string;
  owner_name?: string;
  project_name?: string;
  spend_limit: number;
  current_spend: number;
}

interface User {
  id: number;
  nickname: string;
  username: string;
  status: string;
}

interface Project {
  id: number;
  name: string;
  client_name: string;
  status: string;
}

interface BatchOperationsProps {
  open: boolean;
  onClose: () => void;
  selectedAccounts: AdAccount[];
  onOperationComplete: () => void;
}

// 操作类型
const operationTypes = [
  "change_status",
  "assign_user",
  "assign_project",
  "adjust_budget",
  "pause_all",
  "activate_all",
  "export_data",
  "delete_accounts",
] as const;

type OperationType = (typeof operationTypes)[number];

// 操作配置
const operationConfigs: Record<OperationType, {
  title: string;
  description: string;
  icon: React.ReactNode;
  requiresConfirmation: boolean;
}> = {
  change_status: {
    title: "批量修改状态",
    description: "修改选中账户的状态",
    icon: <Activity className="w-5 h-5" />,
    requiresConfirmation: false,
  },
  assign_user: {
    title: "批量分配负责人",
    description: "为选中账户指定新的负责人",
    icon: <Users className="w-5 h-5" />,
    requiresConfirmation: false,
  },
  assign_project: {
    title: "批量分配项目",
    description: "为选中账户指定所属项目",
    icon: <FileText className="w-5 h-5" />,
    requiresConfirmation: false,
  },
  adjust_budget: {
    title: "批量调整预算",
    description: "调整选中账户的消耗限额",
    icon: <DollarSign className="w-5 h-5" />,
    requiresConfirmation: true,
  },
  pause_all: {
    title: "批量暂停投放",
    description: "暂停所有选中账户的投放",
    icon: <Settings className="w-5 h-5" />,
    requiresConfirmation: true,
  },
  activate_all: {
    title: "批量激活投放",
    description: "激活所有选中账户的投放",
    icon: <CheckCircle className="w-5 h-5" />,
    requiresConfirmation: false,
  },
  export_data: {
    title: "批量导出数据",
    description: "导出选中账户的详细数据报告",
    icon: <CreditCard className="w-5 h-5" />,
    requiresConfirmation: false,
  },
  delete_accounts: {
    title: "批量删除账户",
    description: "删除选中的广告账户（此操作不可恢复）",
    icon: <AlertTriangle className="w-5 h-5 text-red-500" />,
    requiresConfirmation: true,
  },
};

// Zod Schema - 使用 discriminated union
const batchOperationSchema = z.discriminatedUnion("operation", [
  z.object({
    operation: z.literal("change_status"),
    status: z.string().min(1, "请选择状态"),
  }),
  z.object({
    operation: z.literal("assign_user"),
    user_id: z.string().optional(),
  }),
  z.object({
    operation: z.literal("assign_project"),
    project_id: z.string().optional(),
  }),
  z.object({
    operation: z.literal("adjust_budget"),
    budget_type: z.enum(["increase", "decrease", "percentage", "set"], {
      required_error: "请选择调整类型",
    }),
    budget_value: z.number().min(0, "金额/百分比必须大于等于0"),
  }),
  z.object({
    operation: z.literal("pause_all"),
    confirmed: z.boolean().optional(),
  }),
  z.object({
    operation: z.literal("activate_all"),
  }),
  z.object({
    operation: z.literal("export_data"),
    export_format: z.enum(["excel", "csv", "pdf"], {
      required_error: "请选择导出格式",
    }),
    date_range: z.enum(["7d", "30d", "90d", "all"], {
      required_error: "请选择时间范围",
    }),
  }),
  z.object({
    operation: z.literal("delete_accounts"),
    confirmation_text: z.string().refine((val) => val === "DELETE", {
      message: '请输入 "DELETE" 确认删除',
    }),
  }),
]);

type BatchOperationFormValues = z.infer<typeof batchOperationSchema>;

// 默认值 factory
const getDefaultValues = (operation: OperationType): BatchOperationFormValues => {
  switch (operation) {
    case "change_status":
      return { operation: "change_status", status: "" };
    case "assign_user":
      return { operation: "assign_user", user_id: "" };
    case "assign_project":
      return { operation: "assign_project", project_id: "" };
    case "adjust_budget":
      return { operation: "adjust_budget", budget_type: "increase", budget_value: 0 };
    case "pause_all":
      return { operation: "pause_all", confirmed: false };
    case "activate_all":
      return { operation: "activate_all" };
    case "export_data":
      return { operation: "export_data", export_format: "excel", date_range: "7d" };
    case "delete_accounts":
      return { operation: "delete_accounts", confirmation_text: "" };
  }
};

export function BatchOperations({
  open,
  onClose,
  selectedAccounts,
  onOperationComplete,
}: BatchOperationsProps) {
  const queryClient = useQueryClient();

  // Form setup
  const form = useForm<BatchOperationFormValues>({
    resolver: zodResolver(batchOperationSchema),
    defaultValues: getDefaultValues("change_status"),
  });

  const operation = form.watch("operation");
  const currentConfig = operationConfigs[operation];

  // 获取用户列表
  const { data: usersResponse } = useQuery({
    queryKey: ["users", "pitcher,account_manager"],
    queryFn: () => apiGet<{ data: User[] }>("/api/v1/users", { role: "pitcher,account_manager" }),
    enabled: open && operation === "assign_user",
  });
  const users = usersResponse?.data ?? [];

  // 获取项目列表
  const { data: projectsResponse } = useQuery({
    queryKey: ["projects", "active"],
    queryFn: () => apiGet<{ data: Project[] }>("/api/v1/projects", { status: "active" }),
    enabled: open && operation === "assign_project",
  });
  const projects = projectsResponse?.data ?? [];

  // 批量操作 mutation
  const batchMutation = useMutation({
    mutationFn: async (data: BatchOperationFormValues) => {
      const accountIds = selectedAccounts.map(account => account.id);
      const payload = {
        account_ids: accountIds,
        ...data,
      };
      return apiPost<{ data?: { affected_count: number } }>("/api/v1/ad-accounts/batch", payload);
    },
    onSuccess: (response) => {
      const count = response.data?.affected_count ?? selectedAccounts.length;
      toast.success(`批量操作成功，影响 ${count} 个账户`);
      queryClient.invalidateQueries({ queryKey: ["ad-accounts"] });
      onOperationComplete();
      onClose();
    },
    onError: (error) => {
      if (isApiError(error)) {
        toast.error(error.message || "批量操作失败");
      } else {
        toast.error("批量操作失败");
      }
    },
  });

  // 操作类型变化时重置表单
  const handleOperationChange = (newOperation: OperationType) => {
    form.reset(getDefaultValues(newOperation));
  };

  // 提交处理
  const onSubmit = (values: BatchOperationFormValues) => {
    batchMutation.mutate(values);
  };

  // Dialog 打开时重置
  useEffect(() => {
    if (open) {
      form.reset(getDefaultValues("change_status"));
    }
  }, [open, form]);

  // 空选择提示
  if (selectedAccounts.length === 0) {
    return (
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量操作</DialogTitle>
            <DialogDescription>
              请先选择要操作的账户
            </DialogDescription>
          </DialogHeader>
          <div className="text-center py-8">
            <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">未选中任何账户</p>
            <p className="text-sm text-gray-500 mt-2">
              请在列表中选择要执行批量操作的账户
            </p>
          </div>
          <DialogFooter>
            <Button onClick={onClose}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {currentConfig.icon}
            {currentConfig.title}
          </DialogTitle>
          <DialogDescription>
            {currentConfig.description} - 已选择 {selectedAccounts.length} 个账户
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 选中的账户列表 */}
            <div className="max-h-32 overflow-y-auto border rounded-lg p-3">
              <div className="text-sm font-medium mb-2">选中的账户：</div>
              <div className="space-y-1">
                {selectedAccounts.map((account) => (
                  <div key={account.id} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{account.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {account.platform.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-gray-500">
                      <span>{account.owner_name || "未分配"}</span>
                      <span>¥{account.current_spend.toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* 操作类型选择 */}
            <FormField
              control={form.control}
              name="operation"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>选择操作类型</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={(value) => {
                      field.onChange(value);
                      handleOperationChange(value as OperationType);
                    }}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {operationTypes.map((key) => (
                        <SelectItem key={key} value={key}>
                          <div className="flex items-center gap-2">
                            {operationConfigs[key].icon}
                            {operationConfigs[key].title}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 操作参数设置 - 条件渲染 */}
            <div className="space-y-4">
              {/* 修改状态 */}
              {operation === "change_status" && (
                <FormField
                  control={form.control}
                  name="status"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>新状态</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="选择状态" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="active">活跃</SelectItem>
                          <SelectItem value="paused">暂停</SelectItem>
                          <SelectItem value="pending">待审核</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              {/* 分配负责人 */}
              {operation === "assign_user" && (
                <FormField
                  control={form.control}
                  name="user_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>选择负责人</FormLabel>
                      <Select
                        value={field.value || "__none__"}
                        onValueChange={(value) => field.onChange(value === "__none__" ? "" : value)}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="选择负责人" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="__none__">取消分配</SelectItem>
                          {users
                            .filter(user => user.status === "active")
                            .map((user) => (
                              <SelectItem key={user.id} value={user.id.toString()}>
                                {user.nickname} ({user.username})
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              {/* 分配项目 */}
              {operation === "assign_project" && (
                <FormField
                  control={form.control}
                  name="project_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>选择项目</FormLabel>
                      <Select
                        value={field.value || "__none__"}
                        onValueChange={(value) => field.onChange(value === "__none__" ? "" : value)}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="选择项目" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="__none__">取消分配</SelectItem>
                          {projects
                            .filter(project => project.status === "active")
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
              )}

              {/* 调整预算 */}
              {operation === "adjust_budget" && (
                <>
                  <FormField
                    control={form.control}
                    name="budget_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>调整类型</FormLabel>
                        <Select value={field.value} onValueChange={field.onChange}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="选择调整类型" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="increase">按金额增加</SelectItem>
                            <SelectItem value="decrease">按金额减少</SelectItem>
                            <SelectItem value="percentage">按百分比调整</SelectItem>
                            <SelectItem value="set">设置为固定值</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="budget_value"
                    render={({ field }) => {
                      const budgetType = form.watch("budget_type");
                      return (
                        <FormItem>
                          <FormLabel>
                            {budgetType === "percentage" ? "调整百分比 (%)" : "调整金额 (¥)"}
                          </FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              {...field}
                              value={field.value ?? ""}
                              onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                              placeholder={
                                budgetType === "percentage"
                                  ? "输入百分比，如：10 表示增加10%"
                                  : "输入金额"
                              }
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      );
                    }}
                  />
                </>
              )}

              {/* 导出数据 */}
              {operation === "export_data" && (
                <>
                  <FormField
                    control={form.control}
                    name="export_format"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>导出格式</FormLabel>
                        <Select value={field.value} onValueChange={field.onChange}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="选择导出格式" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="excel">Excel (.xlsx)</SelectItem>
                            <SelectItem value="csv">CSV (.csv)</SelectItem>
                            <SelectItem value="pdf">PDF 报告 (.pdf)</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="date_range"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>时间范围</FormLabel>
                        <Select value={field.value} onValueChange={field.onChange}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="选择时间范围" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="7d">最近7天</SelectItem>
                            <SelectItem value="30d">最近30天</SelectItem>
                            <SelectItem value="90d">最近90天</SelectItem>
                            <SelectItem value="all">全部历史</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </>
              )}

              {/* 删除确认 */}
              {operation === "delete_accounts" && (
                <>
                  <Alert>
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                    <AlertDescription className="text-red-600">
                      <strong>警告：此操作不可恢复！</strong>
                      <br />
                      删除账户将同时删除所有相关数据，包括投放记录、消耗历史等。
                    </AlertDescription>
                  </Alert>
                  <FormField
                    control={form.control}
                    name="confirmation_text"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          请输入 &quot;DELETE&quot; 确认删除操作
                        </FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="输入 DELETE" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </>
              )}

              {/* 暂停/激活确认 */}
              {(operation === "pause_all" || operation === "adjust_budget") && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    此操作将影响 {selectedAccounts.length} 个账户，请确认是否继续？
                  </AlertDescription>
                </Alert>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button
                type="submit"
                disabled={
                  batchMutation.isPending ||
                  (operation === "delete_accounts" && form.watch("confirmation_text") !== "DELETE")
                }
                variant={operation === "delete_accounts" ? "destructive" : "default"}
              >
                {batchMutation.isPending ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    执行中...
                  </>
                ) : (
                  "执行操作"
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
