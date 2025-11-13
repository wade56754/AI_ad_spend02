"use client";

import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
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

// 类型定义
interface AdAccount {
  id: number;
  account_name: string;
  platform: string;
  account_status: string;
  assigned_user_name?: string;
  project_name?: string;
  spending_limit: number;
  current_spend: number;
}

interface User {
  id: number;
  nickname: string;
  username: string;
}

interface Project {
  id: number;
  name: string;
  client_name: string;
}

interface BatchOperationsProps {
  open: boolean;
  onClose: () => void;
  selectedAccounts: AdAccount[];
  onOperationComplete: () => void;
}

type OperationType =
  | "change_status"
  | "assign_user"
  | "assign_project"
  | "adjust_budget"
  | "pause_all"
  | "activate_all"
  | "export_data"
  | "delete_accounts";

export function BatchOperations({
  open,
  onClose,
  selectedAccounts,
  onOperationComplete,
}: BatchOperationsProps) {
  const [operation, setOperation] = useState<OperationType>("change_status");
  const [loading, setLoading] = useState(false);
  const [confirmRequired, setConfirmRequired] = useState(false);
  const [operationData, setOperationData] = useState<any>({});
  const [users, setUsers] = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);

  // 操作配置
  const operationConfigs = {
    change_status: {
      title: "批量修改状态",
      description: "修改选中账户的状态",
      icon: <Activity className="w-5 h-5" />,
      requiresConfirmation: false,
      fields: ["status"],
    },
    assign_user: {
      title: "批量分配负责人",
      description: "为选中账户指定新的负责人",
      icon: <Users className="w-5 h-5" />,
      requiresConfirmation: false,
      fields: ["user"],
    },
    assign_project: {
      title: "批量分配项目",
      description: "为选中账户指定所属项目",
      icon: <FileText className="w-5 h-5" />,
      requiresConfirmation: false,
      fields: ["project"],
    },
    adjust_budget: {
      title: "批量调整预算",
      description: "调整选中账户的消耗限额",
      icon: <DollarSign className="w-5 h-5" />,
      requiresConfirmation: true,
      fields: ["budget_type", "budget_value"],
    },
    pause_all: {
      title: "批量暂停投放",
      description: "暂停所有选中账户的投放",
      icon: <Settings className="w-5 h-5" />,
      requiresConfirmation: true,
      fields: [],
    },
    activate_all: {
      title: "批量激活投放",
      description: "激活所有选中账户的投放",
      icon: <CheckCircle className="w-5 h-5" />,
      requiresConfirmation: false,
      fields: [],
    },
    export_data: {
      title: "批量导出数据",
      description: "导出选中账户的详细数据报告",
      icon: <CreditCard className="w-5 h-5" />,
      requiresConfirmation: false,
      fields: ["export_format", "date_range"],
    },
    delete_accounts: {
      title: "批量删除账户",
      description: "删除选中的广告账户（此操作不可恢复）",
      icon: <AlertTriangle className="w-5 h-5 text-red-500" />,
      requiresConfirmation: true,
      fields: ["confirmation_text"],
    },
  };

  const currentConfig = operationConfigs[operation];

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      const response = await fetch("/api/v1/users?role=media_buyer,account_manager");
      const result = await response.json();
      if (result.success) {
        setUsers(result.data);
      }
    } catch (error) {
      console.error("获取用户列表失败:", error);
    }
  };

  // 获取项目列表
  const fetchProjects = async () => {
    try {
      const response = await fetch("/api/v1/projects?status=active");
      const result = await response.json();
      if (result.success) {
        setProjects(result.data);
      }
    } catch (error) {
      console.error("获取项目列表失败:", error);
    }
  };

  // 执行批量操作
  const handleExecuteOperation = async () => {
    if (confirmRequired && !operationData.confirmed) {
      setOperationData({ ...operationData, confirmed: true });
      return;
    }

    setLoading(true);
    try {
      const accountIds = selectedAccounts.map(account => account.id);
      const payload = {
        account_ids: accountIds,
        operation,
        ...operationData,
      };

      const response = await fetch("/api/v1/ad-accounts/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(`批量操作成功，影响 ${result.data.affected_count} 个账户`);
        onOperationComplete();
        onClose();
      } else {
        const error = await response.json();
        toast.error(error.message || "批量操作失败");
      }
    } catch (error) {
      console.error("批量操作错误:", error);
      toast.error("批量操作失败");
    } finally {
      setLoading(false);
    }
  };

  // 重置操作数据
  const resetOperationData = () => {
    setOperationData({});
    setConfirmRequired(false);
  };

  // 操作类型变化时重置数据
  const handleOperationChange = (newOperation: OperationType) => {
    setOperation(newOperation);
    resetOperationData();
    setConfirmRequired(operationConfigs[newOperation].requiresConfirmation);
  };

  useEffect(() => {
    if (open) {
      fetchUsers();
      fetchProjects();
      resetOperationData();
    }
  }, [open]);

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

        {/* 选中的账户列表 */}
        <div className="space-y-4">
          <div className="max-h-32 overflow-y-auto border rounded-lg p-3">
            <div className="text-sm font-medium mb-2">选中的账户：</div>
            <div className="space-y-1">
              {selectedAccounts.map((account) => (
                <div key={account.id} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{account.account_name}</span>
                    <Badge variant="outline" className="text-xs">
                      {account.platform.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-gray-500">
                    <span>{account.assigned_user_name || "未分配"}</span>
                    <span>¥{account.current_spend.toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* 操作类型选择 */}
          <div>
            <Label>选择操作类型</Label>
            <Select value={operation} onValueChange={handleOperationChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(operationConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    <div className="flex items-center gap-2">
                      {config.icon}
                      {config.title}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 操作参数设置 */}
          <div className="space-y-4">
            {/* 修改状态 */}
            {operation === "change_status" && (
              <div>
                <Label>新状态</Label>
                <Select
                  value={operationData.status}
                  onValueChange={(value) => setOperationData({ ...operationData, status: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择状态" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">活跃</SelectItem>
                    <SelectItem value="paused">暂停</SelectItem>
                    <SelectItem value="pending">待审核</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* 分配负责人 */}
            {operation === "assign_user" && (
              <div>
                <Label>选择负责人</Label>
                <Select
                  value={operationData.user_id}
                  onValueChange={(value) => setOperationData({ ...operationData, user_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择负责人" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">取消分配</SelectItem>
                    {users
                      .filter(user => user.status === "active")
                      .map((user) => (
                      <SelectItem key={user.id} value={user.id.toString()}>
                        {user.nickname} ({user.username})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* 分配项目 */}
            {operation === "assign_project" && (
              <div>
                <Label>选择项目</Label>
                <Select
                  value={operationData.project_id}
                  onValueChange={(value) => setOperationData({ ...operationData, project_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">取消分配</SelectItem>
                    {projects
                      .filter(project => project.status === "active")
                      .map((project) => (
                      <SelectItem key={project.id} value={project.id.toString()}>
                        {project.name} - {project.client_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* 调整预算 */}
            {operation === "adjust_budget" && (
              <div className="space-y-4">
                <div>
                  <Label>调整类型</Label>
                  <Select
                    value={operationData.budget_type}
                    onValueChange={(value) => setOperationData({ ...operationData, budget_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择调整类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="increase">按金额增加</SelectItem>
                      <SelectItem value="decrease">按金额减少</SelectItem>
                      <SelectItem value="percentage">按百分比调整</SelectItem>
                      <SelectItem value="set">设置为固定值</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>
                    {operationData.budget_type === "percentage" ? "调整百分比 (%)" : "调整金额 (¥)"}
                  </Label>
                  <Input
                    type="number"
                    value={operationData.budget_value}
                    onChange={(e) => setOperationData({
                      ...operationData,
                      budget_value: parseFloat(e.target.value) || 0
                    })}
                    placeholder={
                      operationData.budget_type === "percentage"
                        ? "输入百分比，如：10 表示增加10%"
                        : "输入金额"
                    }
                  />
                </div>
              </div>
            )}

            {/* 导出数据 */}
            {operation === "export_data" && (
              <div className="space-y-4">
                <div>
                  <Label>导出格式</Label>
                  <Select
                    value={operationData.export_format}
                    onValueChange={(value) => setOperationData({ ...operationData, export_format: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择导出格式" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="excel">Excel (.xlsx)</SelectItem>
                      <SelectItem value="csv">CSV (.csv)</SelectItem>
                      <SelectItem value="pdf">PDF 报告 (.pdf)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>时间范围</Label>
                  <Select
                    value={operationData.date_range}
                    onValueChange={(value) => setOperationData({ ...operationData, date_range: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择时间范围" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="7d">最近7天</SelectItem>
                      <SelectItem value="30d">最近30天</SelectItem>
                      <SelectItem value="90d">最近90天</SelectItem>
                      <SelectItem value="all">全部历史</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}

            {/* 删除确认 */}
            {operation === "delete_accounts" && (
              <div className="space-y-4">
                <Alert>
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <AlertDescription className="text-red-600">
                    <strong>警告：此操作不可恢复！</strong>
                    <br />
                    删除账户将同时删除所有相关数据，包括投放记录、消耗历史等。
                  </AlertDescription>
                </Alert>
                <div>
                  <Label>
                    请输入 "DELETE" 确认删除操作
                  </Label>
                  <Input
                    value={operationData.confirmation_text}
                    onChange={(e) => setOperationData({
                      ...operationData,
                      confirmation_text: e.target.value
                    })}
                    placeholder="输入 DELETE"
                  />
                </div>
              </div>
            )}

            {/* 确认操作 */}
            {confirmRequired && operation !== "delete_accounts" && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  此操作将影响 {selectedAccounts.length} 个账户，请确认是否继续？
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button
            onClick={handleExecuteOperation}
            disabled={loading || (operation === "delete_accounts" && operationData.confirmation_text !== "DELETE")}
            variant={operation === "delete_accounts" ? "destructive" : "default"}
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                执行中...
              </>
            ) : (
              <>
                {confirmRequired && !operationData.confirmed ? "确认操作" : "执行操作"}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}