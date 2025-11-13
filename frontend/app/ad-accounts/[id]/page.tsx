"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { PageTemplate } from "@/components/layout/page-template";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  ArrowLeft,
  Edit,
  Save,
  CreditCard,
  Activity,
  TrendingUp,
  Users,
  DollarSign,
  Eye,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Download,
  Calendar,
  Clock,
  Target,
  BarChart3,
  PieChart,
  LineChart,
} from "lucide-react";
import {
  LineChart as RechartsLineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { toast } from "sonner";
import { format, subDays } from "date-fns";
import { zhCN } from "date-fns/locale";

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
  performance_metrics: {
    total_spend: number;
    total_follows: number;
    total_conversions: number;
    avg_cpl: number;
    avg_cpa: number;
    avg_roas: number;
    last_7d_spend: number;
    last_30d_spend: number;
  };
  health_status: {
    risk_level: "low" | "medium" | "high";
    issues: string[];
    recommendations: string[];
    score: number;
  };
  recent_activity: Array<{
    date: string;
    action: string;
    description: string;
    user: string;
  }>;
  spending_trend: Array<{
    date: string;
    spend: number;
    follows: number;
    conversions: number;
  }>;
  top_campaigns: Array<{
    name: string;
    spend: number;
    follows: number;
    roas: number;
  }>;
  charging_history: Array<{
    date: string;
    amount: number;
    balance_before: number;
    balance_after: number;
    operator: string;
    status: string;
  }>;
}

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1", "#d084d0"];

export default function AdAccountDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [account, setAccount] = useState<AdAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<AdAccount>>({});

  // 模拟数据
  const mockAccount: AdAccount = {
    id: parseInt(params.id as string),
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
    notes: "主要投放账户，表现良好，ROI稳定在3.2以上",
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2025-01-11T18:45:00Z",
    performance_metrics: {
      total_spend: 45000,
      total_follows: 1250,
      total_conversions: 325,
      avg_cpl: 36,
      avg_cpa: 138,
      avg_roas: 3.2,
      last_7d_spend: 2100,
      last_30d_spend: 8500,
    },
    health_status: {
      risk_level: "low",
      issues: [],
      recommendations: ["可以考虑适当增加预算以获得更多流量"],
      score: 85,
    },
    recent_activity: [
      {
        date: "2025-01-11T18:45:00Z",
        action: "广告投放",
        description: "新广告系列"春季促销"开始投放",
        user: "张三",
      },
      {
        date: "2025-01-10T14:20:00Z",
        action: "账户充值",
        description: "充值 $5,000",
        user: "财务部",
      },
      {
        date: "2025-01-09T09:15:00Z",
        action: "调整预算",
        description: "日预算从 $200 调整为 $250",
        user: "张三",
      },
    ],
    spending_trend: [
      { date: "2025-01-06", spend: 280, follows: 12, conversions: 3 },
      { date: "2025-01-07", spend: 320, follows: 15, conversions: 4 },
      { date: "2025-01-08", spend: 290, follows: 11, conversions: 3 },
      { date: "2025-01-09", spend: 350, follows: 18, conversions: 5 },
      { date: "2025-01-10", spend: 410, follows: 20, conversions: 6 },
      { date: "2025-01-11", spend: 450, follows: 24, conversions: 7 },
      { date: "2025-01-12", spend: 380, follows: 19, conversions: 5 },
    ],
    top_campaigns: [
      { name: "春季促销活动", spend: 3200, follows: 180, roas: 3.8 },
      { name: "新品推广", spend: 2100, follows: 120, roas: 2.9 },
      { name: "品牌建设", spend: 1500, follows: 85, roas: 2.1 },
      { name: "转化优化", spend: 700, follows: 42, roas: 4.2 },
    ],
    charging_history: [
      {
        date: "2025-01-10T14:20:00Z",
        amount: 5000,
        balance_before: -2500,
        balance_after: 2500,
        operator: "财务部",
        status: "completed",
      },
      {
        date: "2024-12-28T10:15:00Z",
        amount: 3000,
        balance_before: -500,
        balance_after: 2500,
        operator: "财务部",
        status: "completed",
      },
    ],
  };

  // 获取账户详情
  const fetchAccountDetail = async () => {
    setLoading(true);
    try {
      // 实际应该调用API
      // const response = await fetch(`/api/v1/ad-accounts/${params.id}`);
      // const result = await response.json();

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800));

      setAccount(mockAccount);
      setEditForm(mockAccount);
    } catch (error) {
      toast.error("获取账户详情失败");
      console.error("获取账户详情错误:", error);
    } finally {
      setLoading(false);
    }
  };

  // 保存编辑
  const handleSave = async () => {
    if (!account) return;

    try {
      const response = await fetch(`/api/v1/ad-accounts/${account.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm),
      });

      if (response.ok) {
        toast.success("账户信息更新成功");
        setIsEditing(false);
        fetchAccountDetail();
      }
    } catch (error) {
      toast.error("更新失败");
    }
  };

  // 状态显示组件
  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { icon: CheckCircle, color: "text-green-600", bg: "bg-green-100", text: "活跃" },
      paused: { icon: AlertTriangle, color: "text-yellow-600", bg: "bg-yellow-100", text: "暂停" },
      banned: { icon: XCircle, color: "text-red-600", bg: "bg-red-100", text: "封禁" },
      pending: { icon: RefreshCw, color: "text-blue-600", bg: "bg-blue-100", text: "待审核" },
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    const Icon = config.icon;

    return (
      <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${config.bg}`}>
        <Icon className={`w-3 h-3 ${config.color}`} />
        <span className={`text-xs font-medium ${config.color}`}>{config.text}</span>
      </div>
    );
  };

  // 风险等级显示
  const getRiskBadge = (riskLevel: string) => {
    const riskConfig = {
      low: { color: "text-green-600", bg: "bg-green-100", text: "低风险" },
      medium: { color: "text-yellow-600", bg: "bg-yellow-100", text: "中风险" },
      high: { color: "text-red-600", bg: "bg-red-100", text: "高风险" },
    };

    const config = riskConfig[riskLevel as keyof typeof riskConfig];
    return (
      <div className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
        {config.text}
      </div>
    );
  };

  useEffect(() => {
    if (params.id) {
      fetchAccountDetail();
    }
  }, [params.id]);

  if (loading || !account) {
    return (
      <PageTemplate title="账户详情" description="加载中...">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      </PageTemplate>
    );
  }

  return (
    <PageTemplate
      title={account.account_name}
      description={
        <div className="flex items-center gap-2">
          {getStatusBadge(account.account_status)}
          <span className="text-gray-500">|</span>
          <Badge variant="outline" className="bg-purple-50 text-purple-700">
            {account.platform.toUpperCase()}
          </Badge>
          <span className="text-gray-500">|</span>
          {getRiskBadge(account.health_status.risk_level)}
        </div>
      }
      breadcrumbs={[
        { label: "广告账户管理", href: "/ad-accounts" },
        { label: account.account_name },
      ]}
    >
      <div className="space-y-6">
        {/* 头部操作栏 */}
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回列表
            </Button>
          </div>
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button variant="outline" onClick={() => setIsEditing(false)}>
                  取消
                </Button>
                <Button onClick={handleSave}>
                  <Save className="w-4 h-4 mr-2" />
                  保存
                </Button>
              </>
            ) : (
              <>
                <Button variant="outline" onClick={() => setIsEditing(true)}>
                  <Edit className="w-4 h-4 mr-2" />
                  编辑
                </Button>
                <Button variant="outline" onClick={() => window.open(`/api/v1/ad-accounts/${account.id}/export`)}>
                  <Download className="w-4 h-4 mr-2" />
                  导出报告
                </Button>
              </>
            )}
          </div>
        </div>

        {/* 基本信息卡片 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              基本信息
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="accountName">账户名称</Label>
                  <Input
                    id="accountName"
                    value={editForm.account_name}
                    onChange={(e) => setEditForm({ ...editForm, account_name: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="accountId">账户ID</Label>
                  <Input
                    id="accountId"
                    value={editForm.account_id}
                    onChange={(e) => setEditForm({ ...editForm, account_id: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="status">状态</Label>
                  <Select
                    value={editForm.account_status}
                    onValueChange={(value: any) => setEditForm({ ...editForm, account_status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">活跃</SelectItem>
                      <SelectItem value="paused">暂停</SelectItem>
                      <SelectItem value="banned">封禁</SelectItem>
                      <SelectItem value="pending">待审核</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="spendingLimit">消耗限额</Label>
                  <Input
                    id="spendingLimit"
                    type="number"
                    value={editForm.spending_limit}
                    onChange={(e) => setEditForm({ ...editForm, spending_limit: parseFloat(e.target.value) })}
                  />
                </div>
                <div>
                  <Label htmlFor="assignedUser">负责人</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder={account.assigned_user_name || "选择负责人"} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">张三</SelectItem>
                      <SelectItem value="2">李四</SelectItem>
                      <SelectItem value="3">王五</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="project">所属项目</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder={account.project_name || "选择项目"} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">春季推广项目</SelectItem>
                      <SelectItem value="2">夏季促销活动</SelectItem>
                      <SelectItem value="3">品牌建设</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="md:col-span-2">
                  <Label htmlFor="notes">备注</Label>
                  <Textarea
                    id="notes"
                    value={editForm.notes}
                    onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                    rows={3}
                  />
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm text-gray-600">账户ID</Label>
                    <p className="font-medium">{account.account_id}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">平台</Label>
                    <p className="capitalize font-medium">{account.platform}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">账户类型</Label>
                    <p className="font-medium">{account.account_type === "business" ? "商业账户" : "个人账户"}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">货币</Label>
                    <p className="font-medium">{account.currency}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">时区</Label>
                    <p className="font-medium">{account.timezone}</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm text-gray-600">负责人</Label>
                    <p className="font-medium">{account.assigned_user_name || "未分配"}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">所属项目</Label>
                    <p className="font-medium">{account.project_name || "未分配"}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">创建时间</Label>
                    <p className="font-medium">
                      {format(new Date(account.creation_time), "yyyy年MM月dd日 HH:mm")}
                    </p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">最后活跃</Label>
                    <p className="font-medium">
                      {format(new Date(account.last_active), "yyyy年MM月dd日 HH:mm")}
                    </p>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">备注</Label>
                    <p className="font-medium">{account.notes || "无"}</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 财务概览 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">当前余额</p>
                  <p className="text-2xl font-bold">¥{account.balance.toLocaleString()}</p>
                </div>
                <CreditCard className="h-8 w-8 text-blue-200" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">总消耗</p>
                  <p className="text-2xl font-bold text-red-600">
                    ¥{account.performance_metrics.total_spend.toLocaleString()}
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
                  <p className="text-sm text-gray-600">新增粉丝</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {account.performance_metrics.total_follows.toLocaleString()}
                  </p>
                </div>
                <Users className="h-8 w-8 text-blue-200" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">平均ROI</p>
                  <p className="text-2xl font-bold text-green-600">
                    {account.performance_metrics.avg_roas.toFixed(2)}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-200" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 详细信息标签页 */}
        <Tabs defaultValue="performance" className="space-y-4">
          <TabsList>
            <TabsTrigger value="performance">表现分析</TabsTrigger>
            <TabsTrigger value="campaigns">广告系列</TabsTrigger>
            <TabsTrigger value="charging">充值记录</TabsTrigger>
            <TabsTrigger value="activity">操作历史</TabsTrigger>
            <TabsTrigger value="health">健康状态</TabsTrigger>
          </TabsList>

          <TabsContent value="performance">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 消耗趋势 */}
              <Card>
                <CardHeader>
                  <CardTitle>7天消耗趋势</CardTitle>
                  <CardDescription>最近一周的消耗和转化情况</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={account.spending_trend}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="spend"
                        stroke="#ef4444"
                        name="消耗金额(¥)"
                        strokeWidth={2}
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="follows"
                        stroke="#3b82f6"
                        name="新增粉丝"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* 关键指标 */}
              <Card>
                <CardHeader>
                  <CardTitle>关键指标</CardTitle>
                  <CardDescription>账户的整体表现数据</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">平均单粉成本 (CPL)</span>
                      <span className="font-semibold">¥{account.performance_metrics.avg_cpl.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">平均转化成本 (CPA)</span>
                      <span className="font-semibold">¥{account.performance_metrics.avg_cpa.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">总转化数</span>
                      <span className="font-semibold">{account.performance_metrics.total_conversions}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">最近7天消耗</span>
                      <span className="font-semibold">¥{account.performance_metrics.last_7d_spend.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">最近30天消耗</span>
                      <span className="font-semibold">¥{account.performance_metrics.last_30d_spend.toLocaleString()}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="campaigns">
            <Card>
              <CardHeader>
                <CardTitle>Top 广告系列</CardTitle>
                <CardDescription>按消耗金额排序的主要广告系列</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={account.top_campaigns}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="spend" fill="#8884d8" name="消耗金额(¥)" />
                    <Bar yAxisId="right" dataKey="follows" fill="#82ca9d" name="新增粉丝" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="charging">
            <Card>
              <CardHeader>
                <CardTitle>充值记录</CardTitle>
                <CardDescription>账户的充值历史记录</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {account.charging_history.map((record, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">充值 ¥{record.amount.toLocaleString()}</p>
                          <p className="text-sm text-gray-600">
                            操作人: {record.operator} |
                            {format(new Date(record.date), "yyyy年MM月dd日 HH:mm")}
                          </p>
                        </div>
                        <Badge variant={record.status === "completed" ? "default" : "destructive"}>
                          {record.status === "completed" ? "已完成" : "失败"}
                        </Badge>
                      </div>
                      <div className="mt-2 text-sm text-gray-600">
                        余额变化: ¥{record.balance_before.toLocaleString()} → ¥{record.balance_after.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity">
            <Card>
              <CardHeader>
                <CardTitle>操作历史</CardTitle>
                <CardDescription>账户的最近操作记录</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {account.recent_activity.map((activity, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{activity.action}</span>
                          <span className="text-sm text-gray-500">
                            {format(new Date(activity.date), "MM/dd HH:mm")}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{activity.description}</p>
                        <p className="text-xs text-gray-500">操作人: {activity.user}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="health">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 健康评分 */}
              <Card>
                <CardHeader>
                  <CardTitle>健康评分</CardTitle>
                  <CardDescription>账户整体健康状态评估</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center">
                    <div className="relative">
                      <div className="text-6xl font-bold text-blue-600">
                        {account.health_status.score}
                      </div>
                      <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-sm text-gray-600">
                        综合评分
                      </div>
                    </div>
                  </div>
                  <div className="mt-12 text-center">
                    {getRiskBadge(account.health_status.risk_level)}
                  </div>
                </CardContent>
              </Card>

              {/* 风险和建议 */}
              <Card>
                <CardHeader>
                  <CardTitle>风险与建议</CardTitle>
                  <CardDescription>AI分析的风险点和优化建议</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {account.health_status.issues.length > 0 && (
                      <div>
                        <h4 className="font-medium text-orange-600 mb-2">风险点</h4>
                        <ul className="space-y-1">
                          {account.health_status.issues.map((issue, index) => (
                            <li key={index} className="text-sm flex items-start gap-2">
                              <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                              <span>{issue}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {account.health_status.recommendations.length > 0 && (
                      <div>
                        <h4 className="font-medium text-green-600 mb-2">优化建议</h4>
                        <ul className="space-y-1">
                          {account.health_status.recommendations.map((rec, index) => (
                            <li key={index} className="text-sm flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </PageTemplate>
  );
}