"use client";

import React, { useState, useEffect } from "react";
import { PageTemplate } from "@/components/layout/page-template";
import { DataTable } from "@/components/ui/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Plus,
  Search,
  Filter,
  Download,
  RefreshCw,
  Edit,
  Trash2,
  Eye,
  CreditCard,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  MoreHorizontal,
  Users,
  DollarSign,
  TrendingUp,
  Calendar,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { format, subDays } from "date-fns";
import { zhCN } from "date-fns/locale";
import { AdAccountForm } from "@/components/ad-accounts/ad-account-form";
import { BatchOperations } from "@/components/ad-accounts/batch-operations";

// 类型定义
interface AdAccount {
  id: number;
  account_name: string;
  platform: "facebook" | "tiktok" | "google" | "twitter";
  account_id: string;
  account_status: "active" | "paused" | "banned" | "pending";
  account_type: "personal" | "business";
  currency: string;
  timezone: string;
  spending_limit: number;
  current_spend: number;
  balance: number;
  creation_time: string;
  last_active: string;
  assigned_user_id?: number;
  assigned_user_name?: string;
  project_id?: number;
  project_name?: string;
  notes: string;
  created_at: string;
  updated_at: string;
  performance_metrics?: {
    total_spend: number;
    total_follows: number;
    avg_cpl: number;
    avg_roas: number;
    last_7d_spend: number;
    last_30d_spend: number;
  };
  health_status?: {
    risk_level: "low" | "medium" | "high";
    issues: string[];
    recommendations: string[];
  };
}

// 列定义
const columns = [
  {
    id: "account_name",
    header: "账户名称",
    cell: (row: AdAccount) => (
      <div className="flex flex-col">
        <span className="font-medium">{row.account_name}</span>
        <span className="text-sm text-gray-500">{row.account_id}</span>
      </div>
    ),
  },
  {
    id: "platform",
    header: "平台",
    cell: (row: AdAccount) => (
      <div className="flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${
          row.platform === "facebook" ? "bg-blue-500" :
          row.platform === "tiktok" ? "bg-black" :
          row.platform === "google" ? "bg-red-500" :
          "bg-blue-400"
        }`} />
        <span className="capitalize">{row.platform}</span>
      </div>
    ),
  },
  {
    id: "account_status",
    header: "状态",
    cell: (row: AdAccount) => {
      const statusConfig = {
        active: { icon: CheckCircle, color: "text-green-600", bg: "bg-green-100", text: "活跃" },
        paused: { icon: AlertTriangle, color: "text-yellow-600", bg: "bg-yellow-100", text: "暂停" },
        banned: { icon: XCircle, color: "text-red-600", bg: "bg-red-100", text: "封禁" },
        pending: { icon: RefreshCw, color: "text-blue-600", bg: "bg-blue-100", text: "待审核" },
      };

      const config = statusConfig[row.account_status];
      const Icon = config.icon;

      return (
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${config.bg}`}>
          <Icon className={`w-3 h-3 ${config.color}`} />
          <span className={`text-xs font-medium ${config.color}`}>{config.text}</span>
        </div>
      );
    },
  },
  {
    id: "assigned_user_name",
    header: "负责人",
    cell: (row: AdAccount) => (
      <div className="flex items-center gap-2">
        <Users className="w-4 h-4 text-gray-400" />
        <span>{row.assigned_user_name || "未分配"}</span>
      </div>
    ),
  },
  {
    id: "project_name",
    header: "所属项目",
    cell: (row: AdAccount) => (
      <Badge variant="outline" className="bg-purple-50 text-purple-700">
        {row.project_name || "未分配"}
      </Badge>
    ),
  },
  {
    id: "spending",
    header: "消耗情况",
    cell: (row: AdAccount) => {
      const spendPercentage = (row.current_spend / row.spending_limit) * 100;
      const isNearLimit = spendPercentage > 80;

      return (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span>¥{row.current_spend.toLocaleString()}</span>
            <span className="text-gray-500">/ ¥{row.spending_limit.toLocaleString()}</span>
          </div>
          <div className="w-20 bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                isNearLimit ? "bg-red-500" : spendPercentage > 60 ? "bg-yellow-500" : "bg-green-500"
              }`}
              style={{ width: `${Math.min(spendPercentage, 100)}%` }}
            />
          </div>
          {isNearLimit && (
            <div className="flex items-center gap-1 text-xs text-red-600">
              <AlertTriangle className="w-3 h-3" />
              <span>接近限额</span>
            </div>
          )}
        </div>
      );
    },
  },
  {
    id: "performance_metrics",
    header: "7天表现",
    cell: (row: AdAccount) => (
      <div className="text-sm space-y-1">
        <div className="flex items-center gap-2">
          <DollarSign className="w-3 h-3 text-red-500" />
          <span>¥{row.performance_metrics?.last_7d_spend.toLocaleString() || 0}</span>
        </div>
        <div className="flex items-center gap-2">
          <Users className="w-3 h-3 text-blue-500" />
          <span>{row.performance_metrics?.total_follows?.toLocaleString() || 0} 粉</span>
        </div>
        <div className="flex items-center gap-2">
          <TrendingUp className="w-3 h-3 text-green-500" />
          <span>ROI {(row.performance_metrics?.avg_roas || 0).toFixed(1)}</span>
        </div>
      </div>
    ),
  },
  {
    id: "health_status",
    header: "健康状态",
    cell: (row: AdAccount) => {
      if (!row.health_status) {
        return <span className="text-gray-400 text-sm">未评估</span>;
      }

      const riskConfig = {
        low: { color: "text-green-600", bg: "bg-green-100", text: "良好" },
        medium: { color: "text-yellow-600", bg: "bg-yellow-100", text: "中等" },
        high: { color: "text-red-600", bg: "bg-red-100", text: "高风险" },
      };

      const config = riskConfig[row.health_status.risk_level];

      return (
        <div className="space-y-1">
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
            {config.text}
          </div>
          {row.health_status.issues.length > 0 && (
            <div className="flex items-center gap-1 text-xs text-orange-600">
              <AlertTriangle className="w-3 h-3" />
              <span>{row.health_status.issues.length} 个问题</span>
            </div>
          )}
        </div>
      );
    },
  },
  {
    id: "last_active",
    header: "最后活跃",
    cell: (row: AdAccount) => {
      const lastActive = new Date(row.last_active);
      const now = new Date();
      const daysDiff = Math.floor((now.getTime() - lastActive.getTime()) / (1000 * 60 * 60 * 24));

      let statusColor = "text-gray-500";
      let statusText = format(lastActive, "MM/dd", { locale: zhCN });

      if (daysDiff === 0) {
        statusColor = "text-green-600";
        statusText = "今天";
      } else if (daysDiff <= 3) {
        statusColor = "text-blue-600";
        statusText = `${daysDiff}天前`;
      } else if (daysDiff <= 7) {
        statusColor = "text-yellow-600";
        statusText = `${daysDiff}天前`;
      } else {
        statusColor = "text-red-600";
        statusText = `${daysDiff}天前`;
      }

      return (
        <div className={`text-sm ${statusColor}`}>
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            <span>{statusText}</span>
          </div>
        </div>
      );
    },
  },
  {
    id: "actions",
    header: "操作",
    cell: (row: AdAccount) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm">
            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>操作</DropdownMenuLabel>
          <DropdownMenuItem>
            <Eye className="w-4 h-4 mr-2" />
            查看详情
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => {
            const account = filteredAccounts.find(a => a.id === row.id);
            if (account) {
              setEditData(account);
              setShowCreateDialog(true);
            }
          }}>
            <Edit className="w-4 h-4 mr-2" />
            编辑账户
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem>
            <CreditCard className="w-4 h-4 mr-2" />
            充值记录
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Activity className="w-4 h-4 mr-2" />
            消耗记录
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem className="text-red-600">
            <Trash2 className="w-4 h-4 mr-2" />
            删除账户
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function AdAccountsPage() {
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedUser, setSelectedUser] = useState<string>("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showBatchDialog, setShowBatchDialog] = useState(false);
  const [selectedAccounts, setSelectedAccounts] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // 平台选项
  const platformOptions = [
    { value: "all", label: "所有平台" },
    { value: "facebook", label: "Facebook" },
    { value: "tiktok", label: "TikTok" },
    { value: "google", label: "Google" },
    { value: "twitter", label: "Twitter" },
  ];

  // 状态选项
  const statusOptions = [
    { value: "all", label: "所有状态" },
    { value: "active", label: "活跃" },
    { value: "paused", label: "暂停" },
    { value: "banned", label: "封禁" },
    { value: "pending", label: "待审核" },
  ];

  // 模拟数据
  const mockAccounts: AdAccount[] = [
    {
      id: 1,
      account_name: "Facebook Main Account",
      platform: "facebook",
      account_id: "act_12345678901234567",
      account_status: "active",
      account_type: "business",
      currency: "USD",
      timezone: "Asia/Shanghai",
      spending_limit: 10000,
      current_spend: 7500,
      balance: 2500,
      creation_time: "2024-01-15T10:30:00Z",
      last_active: "2025-01-11T18:45:00Z",
      assigned_user_name: "张三",
      project_name: "春季推广项目",
      notes: "主要投放账户，表现良好",
      created_at: "2024-01-15T10:30:00Z",
      updated_at: "2025-01-11T18:45:00Z",
      performance_metrics: {
        total_spend: 45000,
        total_follows: 1250,
        avg_cpl: 36,
        avg_roas: 3.2,
        last_7d_spend: 2100,
        last_30d_spend: 8500,
      },
      health_status: {
        risk_level: "low",
        issues: [],
        recommendations: ["可以考虑适当增加预算"],
      },
    },
    {
      id: 2,
      account_name: "TikTok Gaming Account",
      platform: "tiktok",
      account_id: "tt_98765432109876543",
      account_status: "paused",
      account_type: "business",
      currency: "USD",
      timezone: "Asia/Shanghai",
      spending_limit: 5000,
      current_spend: 3200,
      balance: 1800,
      creation_time: "2024-02-20T14:15:00Z",
      last_active: "2025-01-08T12:30:00Z",
      assigned_user_name: "李四",
      project_name: "游戏推广",
      notes: "暂停中，等待新素材",
      created_at: "2024-02-20T14:15:00Z",
      updated_at: "2025-01-09T09:20:00Z",
      performance_metrics: {
        total_spend: 18000,
        total_follows: 680,
        avg_cpl: 26.5,
        avg_roas: 4.1,
        last_7d_spend: 800,
        last_30d_spend: 2100,
      },
      health_status: {
        risk_level: "medium",
        issues: ["最近3天消耗下降明显"],
        recommendations: ["检查广告素材表现", "考虑调整出价策略"],
      },
    },
    {
      id: 3,
      account_name: "Google Ads Performance",
      platform: "google",
      account_id: "ga_56789012345678901",
      account_status: "active",
      account_type: "business",
      currency: "USD",
      timezone: "Asia/Shanghai",
      spending_limit: 8000,
      current_spend: 6200,
      balance: 1800,
      creation_time: "2024-03-10T09:45:00Z",
      last_active: "2025-01-12T16:20:00Z",
      assigned_user_name: "王五",
      project_name: "电商转化",
      notes: "搜索广告表现稳定",
      created_at: "2024-03-10T09:45:00Z",
      updated_at: "2025-01-12T16:20:00Z",
      performance_metrics: {
        total_spend: 28000,
        total_follows: 890,
        avg_cpl: 31.5,
        avg_roas: 2.8,
        last_7d_spend: 1800,
        last_30d_spend: 6800,
      },
      health_status: {
        risk_level: "low",
        issues: [],
        recommendations: ["ROI有提升空间，可以优化关键词"],
      },
    },
  ];

  // 获取账户列表
  const fetchAccounts = async () => {
    setLoading(true);
    try {
      // 实际应该调用API
      // const response = await fetch(`/api/v1/ad-accounts?page=${currentPage}&size=10`);
      // const result = await response.json();

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800));

      setAccounts(mockAccounts);
      setTotalCount(mockAccounts.length);
      setTotalPages(Math.ceil(mockAccounts.length / 10));
    } catch (error) {
      toast.error("获取账户列表失败");
      console.error("获取账户列表错误:", error);
    } finally {
      setLoading(false);
    }
  };

  // 搜索和筛选
  const filteredAccounts = accounts.filter(account => {
    const matchesSearch = searchTerm === "" ||
      account.account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      account.account_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      account.assigned_user_name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesPlatform = selectedPlatform === "all" || account.platform === selectedPlatform;
    const matchesStatus = selectedStatus === "all" || account.account_status === selectedStatus;
    const matchesUser = selectedUser === "all" || account.assigned_user_name === selectedUser;

    return matchesSearch && matchesPlatform && matchesStatus && matchesUser;
  });

  // 刷新数据
  const handleRefresh = () => {
    fetchAccounts();
  };

  // 导出数据
  const handleExport = async () => {
    try {
      const response = await fetch("/api/v1/ad-accounts/export");
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `ad-accounts-${format(new Date(), "yyyyMMdd")}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("导出成功");
      }
    } catch (error) {
      toast.error("导出失败");
    }
  };

  // 批量操作
  const handleBatchOperation = (operation: string) => {
    if (selectedAccounts.length === 0) {
      toast.error("请先选择要操作的账户");
      return;
    }
    setShowBatchDialog(true);
  };

  // 处理账户创建/编辑
  const handleAccountSubmit = async (data: any) => {
    const method = editData ? "PUT" : "POST";
    const url = editData ? `/api/v1/ad-accounts/${editData.id}` : "/api/v1/ad-accounts";

    try {
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        toast.success(`账户${editData ? "更新" : "创建"}成功`);
        fetchAccounts();
      } else {
        throw new Error("操作失败");
      }
    } catch (error) {
      throw error;
    }
  };

  const [editData, setEditData] = useState<any>(null);

  useEffect(() => {
    fetchAccounts();
  }, [currentPage]);

  return (
    <PageTemplate
      title="广告账户管理"
      description="管理和监控所有广告账户的状态和表现"
    >
      <div className="space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">总账户数</p>
                  <p className="text-2xl font-bold">{totalCount}</p>
                </div>
                <CreditCard className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">活跃账户</p>
                  <p className="text-2xl font-bold text-green-600">
                    {accounts.filter(a => a.account_status === "active").length}
                  </p>
                </div>
                <Activity className="h-8 w-8 text-green-200" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">总消耗</p>
                  <p className="text-2xl font-bold text-red-600">
                    ¥{accounts.reduce((sum, a) => sum + a.current_spend, 0).toLocaleString()}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-red-200" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">风险账户</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {accounts.filter(a => a.health_status?.risk_level === "high").length}
                  </p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-200" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 筛选和搜索栏 */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* 搜索框 */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="搜索账户名称、ID或负责人..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* 筛选器 */}
              <div className="flex flex-wrap gap-2">
                <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {platformOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {statusOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={selectedUser} onValueChange={setSelectedUser}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">所有负责人</SelectItem>
                    <SelectItem value="张三">张三</SelectItem>
                    <SelectItem value="李四">李四</SelectItem>
                    <SelectItem value="王五">王五</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* 操作按钮 */}
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleRefresh}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  刷新
                </Button>
                <Button variant="outline" onClick={handleExport}>
                  <Download className="w-4 h-4 mr-2" />
                  导出
                </Button>
                <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="w-4 h-4 mr-2" />
                      新建账户
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md">
                    <DialogHeader>
                      <DialogTitle>新建广告账户</DialogTitle>
                      <DialogDescription>
                        创建新的广告账户，请确保信息准确无误
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="accountName">账户名称</Label>
                        <Input id="accountName" placeholder="输入账户名称" />
                      </div>
                      <div>
                        <Label htmlFor="platform">平台</Label>
                        <Select>
                          <SelectTrigger>
                            <SelectValue placeholder="选择广告平台" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="facebook">Facebook</SelectItem>
                            <SelectItem value="tiktok">TikTok</SelectItem>
                            <SelectItem value="google">Google</SelectItem>
                            <SelectItem value="twitter">Twitter</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="accountId">账户ID</Label>
                        <Input id="accountId" placeholder="输入广告账户ID" />
                      </div>
                      <div>
                        <Label htmlFor="spendingLimit">消耗限额</Label>
                        <Input id="spendingLimit" type="number" placeholder="输入月度消耗限额" />
                      </div>
                      <div>
                        <Label htmlFor="assignedUser">负责人</Label>
                        <Select>
                          <SelectTrigger>
                            <SelectValue placeholder="选择负责人" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="1">张三</SelectItem>
                            <SelectItem value="2">李四</SelectItem>
                            <SelectItem value="3">王五</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                        取消
                      </Button>
                      <Button type="submit">
                        创建账户
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </div>

            {/* 批量操作栏 */}
            {selectedAccounts.length > 0 && (
              <div className="flex items-center justify-between pt-4 border-t">
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={selectedAccounts.length === filteredAccounts.length}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedAccounts(filteredAccounts.map(a => a.id));
                      } else {
                        setSelectedAccounts([]);
                      }
                    }}
                  />
                  <span className="text-sm text-gray-600">
                    已选择 {selectedAccounts.length} 个账户
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBatchOperation("pause")}
                  >
                    暂停投放
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBatchOperation("activate")}
                  >
                    激活投放
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleBatchOperation("delete")}
                  >
                    批量删除
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 账户列表 */}
        <Card>
          <CardContent className="p-0">
            <DataTable
              columns={columns}
              data={filteredAccounts}
              loading={loading}
              selectable
              selectedRows={selectedAccounts}
              onSelectedRowsChange={setSelectedAccounts}
              pagination={{
                currentPage,
                totalPages,
                totalCount,
                onPageChange: setCurrentPage,
              }}
            />
          </CardContent>
        </Card>
      </div>

      {/* 账户创建/编辑表单 */}
      <AdAccountForm
        open={showCreateDialog}
        onClose={() => {
          setShowCreateDialog(false);
          setEditData(null);
        }}
        onSubmit={handleAccountSubmit}
        editData={editData}
        mode={editData ? "edit" : "create"}
      />

      {/* 批量操作对话框 */}
      <BatchOperations
        open={showBatchDialog}
        onClose={() => setShowBatchDialog(false)}
        selectedAccounts={filteredAccounts.filter(account => selectedAccounts.includes(account.id))}
        onOperationComplete={() => {
          setShowBatchDialog(false);
          setSelectedAccounts([]);
          fetchAccounts();
        }}
      />
    </PageTemplate>
  );
}