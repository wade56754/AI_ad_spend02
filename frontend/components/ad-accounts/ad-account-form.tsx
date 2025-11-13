"use client";

import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
} from "lucide-react";
import { toast } from "sonner";

// 类型定义
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

interface AdAccount {
  id?: number;
  account_name: string;
  platform: "facebook" | "tiktok" | "google" | "twitter";
  account_id: string;
  account_type: "personal" | "business";
  currency: string;
  timezone: string;
  spending_limit: number;
  daily_budget?: number;
  account_status: "active" | "paused" | "banned" | "pending";
  assigned_user_id?: number;
  project_id?: number;
  notes: string;
  auto_optimization?: boolean;
  notification_settings?: {
    budget_alert: boolean;
    performance_alert: boolean;
    status_change_alert: boolean;
  };
}

interface AdAccountFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: AdAccount) => Promise<void>;
  editData?: AdAccount;
  mode: "create" | "edit";
}

// 平台配置
const platformConfigs = {
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

export function AdAccountForm({
  open,
  onClose,
  onSubmit,
  editData,
  mode,
}: AdAccountFormProps) {
  const [formData, setFormData] = useState<AdAccount>({
    account_name: "",
    platform: "facebook",
    account_id: "",
    account_type: "business",
    currency: "USD",
    timezone: "Asia/Shanghai",
    spending_limit: 5000,
    daily_budget: undefined,
    account_status: "pending",
    notes: "",
    auto_optimization: false,
    notification_settings: {
      budget_alert: true,
      performance_alert: true,
      status_change_alert: true,
    },
  });

  const [users, setUsers] = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [accountValid, setAccountValid] = useState<boolean | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

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

  // 验证账户ID
  const validateAccountId = async () => {
    if (!formData.account_id || !formData.platform) return;

    setValidating(true);
    setAccountValid(null);

    try {
      const response = await fetch(`/api/v1/ad-accounts/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: formData.platform,
          account_id: formData.account_id,
        }),
      });

      const result = await response.json();
      setAccountValid(result.success && result.data.valid);
    } catch (error) {
      console.error("验证失败:", error);
      setAccountValid(false);
    } finally {
      setValidating(false);
    }
  };

  // 表单验证
  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.account_name.trim()) {
      newErrors.account_name = "账户名称不能为空";
    }

    if (!formData.account_id.trim()) {
      newErrors.account_id = "账户ID不能为空";
    }

    if (accountValid === false) {
      newErrors.account_id = "账户ID无效或已被占用";
    }

    if (!formData.spending_limit || formData.spending_limit <= 0) {
      newErrors.spending_limit = "消耗限额必须大于0";
    }

    if (formData.daily_budget && formData.daily_budget <= 0) {
      newErrors.daily_budget = "日预算必须大于0";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 处理表单提交
  const handleSubmit = async () => {
    if (!validateForm()) {
      toast.error("请检查表单填写是否正确");
      return;
    }

    setLoading(true);
    try {
      await onSubmit(formData);
      toast.success(mode === "create" ? "账户创建成功" : "账户更新成功");
      onClose();
    } catch (error) {
      toast.error("操作失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
      account_name: "",
      platform: "facebook",
      account_id: "",
      account_type: "business",
      currency: "USD",
      timezone: "Asia/Shanghai",
      spending_limit: 5000,
      daily_budget: undefined,
      account_status: "pending",
      notes: "",
      auto_optimization: false,
      notification_settings: {
        budget_alert: true,
        performance_alert: true,
        status_change_alert: true,
      },
    });
    setErrors({});
    setAccountValid(null);
    setShowAdvanced(false);
  };

  // 初始化编辑数据
  useEffect(() => {
    if (editData) {
      setFormData({
        ...editData,
        notification_settings: editData.notification_settings || {
          budget_alert: true,
          performance_alert: true,
          status_change_alert: true,
        },
      });
    } else {
      resetForm();
    }
  }, [editData, open]);

  // 获取数据
  useEffect(() => {
    if (open) {
      fetchUsers();
      fetchProjects();
    }
  }, [open]);

  // 账户ID变化时验证
  useEffect(() => {
    if (formData.account_id && formData.platform) {
      const timer = setTimeout(() => {
        validateAccountId();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [formData.account_id, formData.platform]);

  const platformConfig = platformConfigs[formData.platform];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            {mode === "create" ? "新建广告账户" : "编辑广告账户"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "创建新的广告账户，请确保信息准确无误"
              : "编辑广告账户信息，修改后请保存"
            }
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 平台选择 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">平台信息</CardTitle>
              <CardDescription>选择广告投放平台</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(platformConfigs).map(([key, config]) => (
                  <div
                    key={key}
                    className={`cursor-pointer rounded-lg border-2 p-4 transition-all ${
                      formData.platform === key
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                    onClick={() => setFormData({ ...formData, platform: key as any })}
                  >
                    <div className={`w-3 h-3 rounded-full ${config.color} mb-2`} />
                    <div className="font-medium">{config.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      ID前缀: {config.idPrefix}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">基本信息</CardTitle>
              <CardDescription>账户的基本配置信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="accountName">
                    账户名称 <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="accountName"
                    value={formData.account_name}
                    onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                    placeholder="输入账户名称"
                    className={errors.account_name ? "border-red-500" : ""}
                  />
                  {errors.account_name && (
                    <p className="text-sm text-red-500 mt-1">{errors.account_name}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="accountId">
                    账户ID <span className="text-red-500">*</span>
                  </Label>
                  <div className="relative">
                    <Input
                      id="accountId"
                      value={formData.account_id}
                      onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                      placeholder={`${platformConfig.idPrefix}1234567890`}
                      className={errors.account_id ? "border-red-500" : ""}
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
                  {errors.account_id && (
                    <p className="text-sm text-red-500 mt-1">{errors.account_id}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="accountType">账户类型</Label>
                  <Select
                    value={formData.account_type}
                    onValueChange={(value: any) => setFormData({ ...formData, account_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="personal">个人账户</SelectItem>
                      <SelectItem value="business">商业账户</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="currency">货币</Label>
                  <Select
                    value={formData.currency}
                    onValueChange={(value) => setFormData({ ...formData, currency: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {platformConfig.currencies.map((currency) => (
                        <SelectItem key={currency} value={currency}>
                          {currency}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="timezone">时区</Label>
                  <Select
                    value={formData.timezone}
                    onValueChange={(value) => setFormData({ ...formData, timezone: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Shanghai">Asia/Shanghai</SelectItem>
                      <SelectItem value="Asia/Tokyo">Asia/Tokyo</SelectItem>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="America/New_York">America/New_York</SelectItem>
                      <SelectItem value="Europe/London">Europe/London</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="status">初始状态</Label>
                  <Select
                    value={formData.account_status}
                    onValueChange={(value: any) => setFormData({ ...formData, account_status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">待审核</SelectItem>
                      <SelectItem value="active">活跃</SelectItem>
                      <SelectItem value="paused">暂停</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="assignedUser">负责人</Label>
                  <Select
                    value={formData.assigned_user_id?.toString()}
                    onValueChange={(value) => setFormData({
                      ...formData,
                      assigned_user_id: value ? parseInt(value) : undefined
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择负责人" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">未分配</SelectItem>
                      {users
                        .filter(user => user.status === "active")
                        .map((user) => (
                        <SelectItem key={user.id} value={user.id.toString()}>
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            <span>{user.nickname} ({user.username})</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="project">所属项目</Label>
                  <Select
                    value={formData.project_id?.toString()}
                    onValueChange={(value) => setFormData({
                      ...formData,
                      project_id: value ? parseInt(value) : undefined
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">未分配</SelectItem>
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
              </div>

              <div>
                <Label htmlFor="notes">备注</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="输入账户相关备注信息..."
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          {/* 预算设置 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">预算设置</CardTitle>
              <CardDescription>设置账户的消耗限额和预算</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="spendingLimit">
                    月度消耗限额 <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="spendingLimit"
                    type="number"
                    value={formData.spending_limit}
                    onChange={(e) => setFormData({
                      ...formData,
                      spending_limit: parseFloat(e.target.value) || 0
                    })}
                    placeholder="输入月度消耗限额"
                    className={errors.spending_limit ? "border-red-500" : ""}
                  />
                  {errors.spending_limit && (
                    <p className="text-sm text-red-500 mt-1">{errors.spending_limit}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="dailyBudget">日预算（可选）</Label>
                  <Input
                    id="dailyBudget"
                    type="number"
                    value={formData.daily_budget || ""}
                    onChange={(e) => setFormData({
                      ...formData,
                      daily_budget: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                    placeholder="输入日预算"
                    className={errors.daily_budget ? "border-red-500" : ""}
                  />
                  {errors.daily_budget && (
                    <p className="text-sm text-red-500 mt-1">{errors.daily_budget}</p>
                  )}
                </div>
              </div>

              {formData.daily_budget && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    设置日预算将限制每日消耗，月度消耗限额仍然有效。
                    当前设置日预算为 ¥{formData.daily_budget.toLocaleString()}，
                    月度预计消耗 ¥{(formData.daily_budget * 30).toLocaleString()}。
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* 高级设置 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Settings className="w-5 h-5" />
                高级设置
                <Button
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
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="autoOptimization"
                    checked={formData.auto_optimization}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, auto_optimization: checked as boolean })
                    }
                  />
                  <Label htmlFor="autoOptimization">启用自动优化</Label>
                </div>

                <div className="space-y-3">
                  <Label>通知设置</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="budgetAlert"
                        checked={formData.notification_settings?.budget_alert}
                        onCheckedChange={(checked) =>
                          setFormData({
                            ...formData,
                            notification_settings: {
                              ...formData.notification_settings!,
                              budget_alert: checked as boolean,
                            },
                          })
                        }
                      />
                      <Label htmlFor="budgetAlert">预算告警通知</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="performanceAlert"
                        checked={formData.notification_settings?.performance_alert}
                        onCheckedChange={(checked) =>
                          setFormData({
                            ...formData,
                            notification_settings: {
                              ...formData.notification_settings!,
                              performance_alert: checked as boolean,
                            },
                          })
                        }
                      />
                      <Label htmlFor="performanceAlert">性能异常通知</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="statusChangeAlert"
                        checked={formData.notification_settings?.status_change_alert}
                        onCheckedChange={(checked) =>
                          setFormData({
                            ...formData,
                            notification_settings: {
                              ...formData.notification_settings!,
                              status_change_alert: checked as boolean,
                            },
                          })
                        }
                      />
                      <Label htmlFor="statusChangeAlert">状态变更通知</Label>
                    </div>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>

          {/* 平台特性说明 */}
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
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading || accountValid === false}>
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                {mode === "create" ? "创建中..." : "保存中..."}
              </>
            ) : (
              <>
                {mode === "create" ? "创建账户" : "保存修改"}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}