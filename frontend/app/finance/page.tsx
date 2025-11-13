"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Plus,
  Search,
  Filter,
  Download,
  CreditCard,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Calendar,
  User,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Edit,
  Trash2,
  MoreHorizontal,
  AlertTriangle,
  FileText,
  BarChart3,
  Wallet,
  PiggyBank,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

// 类型定义
interface TopupRequest {
  id: number;
  user_name: string;
  user_role: string;
  account_name: string;
  platform: string;
  amount: number;
  currency: string;
  reason: string;
  status: "pending" | "approved" | "rejected" | "completed";
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
  review_comment?: string;
  receipt_url?: string;
  transaction_id?: string;
  completed_at?: string;
}

interface FinancialSummary {
  total_balance: number;
  currency: string;
  this_month_spending: number;
  last_month_spending: number;
  pending_topups: number;
  approved_topups: number;
  average_approval_time: number;
  success_rate: number;
  projected_spend: number;
}

interface SpendingTrend {
  date: string;
  spending: number;
  topups: number;
  balance: number;
}

interface PlatformSpending {
  platform: string;
  amount: number;
  percentage: number;
  color: string;
}

interface TeamSpending {
  user_name: string;
  role: string;
  total_spent: number;
  budget_utilization: number;
  projects_count: number;
  efficiency_score: number;
}

export default function FinanceManagementPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedRequest, setSelectedRequest] = useState<TopupRequest | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [showRejectionDialog, setShowRejectionDialog] = useState(false);
  const [reviewComment, setReviewComment] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  // 模拟数据
  const [topupRequests, setTopupRequests] = useState<TopupRequest[]>([
    {
      id: 1,
      user_name: "张三",
      user_role: "投手",
      account_name: "Facebook广告账户01",
      platform: "facebook",
      amount: 50000,
      currency: "CNY",
      reason: "新产品推广活动需要增加预算",
      status: "pending",
      created_at: "2025-01-13T10:30:00Z",
    },
    {
      id: 2,
      user_name: "李四",
      user_role: "户管",
      account_name: "TikTok广告账户02",
      platform: "tiktok",
      amount: 30000,
      currency: "CNY",
      reason: "月度常规充值",
      status: "approved",
      created_at: "2025-01-13T09:15:00Z",
      reviewed_at: "2025-01-13T10:20:00Z",
      reviewed_by: "财务经理",
      review_comment: "预算合理，批准充值",
    },
    {
      id: 3,
      user_name: "王五",
      user_role: "投手",
      account_name: "Google Ads账户03",
      platform: "google",
      amount: 80000,
      currency: "CNY",
      reason: "大促活动预算申请",
      status: "completed",
      created_at: "2025-01-12T14:00:00Z",
      reviewed_at: "2025-01-12T16:30:00Z",
      reviewed_by: "财务总监",
      review_comment: "大促预算已批准",
      receipt_url: "/receipts/receipt_001.pdf",
      transaction_id: "TXN20250112001",
      completed_at: "2025-01-13T09:00:00Z",
    },
    {
      id: 4,
      user_name: "赵六",
      user_role: "户管",
      account_name: "Facebook广告账户04",
      platform: "facebook",
      amount: 20000,
      currency: "CNY",
      reason: "测试账户充值",
      status: "rejected",
      created_at: "2025-01-12T11:20:00Z",
      reviewed_at: "2025-01-12T15:45:00Z",
      reviewed_by: "财务经理",
      review_comment: "测试账户无需大额充值，建议使用小额测试",
    },
  ]);

  const [financialSummary] = useState<FinancialSummary>({
    total_balance: 1580000,
    currency: "CNY",
    this_month_spending: 680000,
    last_month_spending: 520000,
    pending_topups: 180000,
    approved_topups: 420000,
    average_approval_time: 2.5,
    success_rate: 92.5,
    projected_spend: 750000,
  });

  const [spendingTrends] = useState<SpendingTrend[]>([
    { date: "1月1日", spending: 15000, topups: 50000, balance: 1485000 },
    { date: "1月2日", spending: 22000, topups: 0, balance: 1463000 },
    { date: "1月3日", spending: 18000, topups: 0, balance: 1445000 },
    { date: "1月4日", spending: 25000, topups: 0, balance: 1420000 },
    { date: "1月5日", spending: 20000, topups: 80000, balance: 1480000 },
    { date: "1月6日", spending: 30000, topups: 0, balance: 1450000 },
    { date: "1月7日", spending: 28000, topups: 0, balance: 1422000 },
    { date: "1月8日", spending: 32000, topups: 100000, balance: 1490000 },
  ]);

  const [platformSpending] = useState<PlatformSpending[]>([
    { platform: "Facebook", amount: 320000, percentage: 47.1, color: "#1877F2" },
    { platform: "TikTok", amount: 180000, percentage: 26.5, color: "#000000" },
    { platform: "Google", amount: 120000, percentage: 17.6, color: "#4285F4" },
    { platform: "Twitter", amount: 60000, percentage: 8.8, color: "#1DA1F2" },
  ]);

  const [teamSpending] = useState<TeamSpending[]>([
    {
      user_name: "张三",
      role: "投手",
      total_spent: 180000,
      budget_utilization: 85,
      projects_count: 8,
      efficiency_score: 92,
    },
    {
      user_name: "李四",
      role: "户管",
      total_spent: 220000,
      budget_utilization: 72,
      projects_count: 12,
      efficiency_score: 88,
    },
    {
      user_name: "王五",
      role: "投手",
      total_spent: 150000,
      budget_utilization: 90,
      projects_count: 6,
      efficiency_score: 95,
    },
    {
      user_name: "赵六",
      role: "户管",
      total_spent: 130000,
      budget_utilization: 65,
      projects_count: 10,
      efficiency_score: 82,
    },
  ]);

  useEffect(() => {
    // 模拟数据加载
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  }, []);

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending": return "bg-yellow-100 text-yellow-700 border-yellow-300";
      case "approved": return "bg-blue-100 text-blue-700 border-blue-300";
      case "rejected": return "bg-red-100 text-red-700 border-red-300";
      case "completed": return "bg-green-100 text-green-700 border-green-300";
      default: return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case "pending": return "待审核";
      case "approved": return "已批准";
      case "rejected": return "已拒绝";
      case "completed": return "已完成";
      default: return "未知";
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending": return <Clock className="w-4 h-4" />;
      case "approved": return <CheckCircle className="w-4 h-4" />;
      case "rejected": return <XCircle className="w-4 h-4" />;
      case "completed": return <CheckCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  // 过滤充值申请
  const filteredRequests = topupRequests.filter(request => {
    const matchesSearch = request.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         request.account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         request.reason.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || request.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // 处理申请批准
  const handleApprove = (request: TopupRequest) => {
    setSelectedRequest(request);
    setShowApprovalDialog(true);
  };

  // 处理申请拒绝
  const handleReject = (request: TopupRequest) => {
    setSelectedRequest(request);
    setShowRejectionDialog(true);
  };

  // 确认批准
  const confirmApprove = () => {
    // 这里调用API更新申请状态
    setTopupRequests(prev =>
      prev.map(req =>
        req.id === selectedRequest?.id
          ? {
              ...req,
              status: "approved",
              reviewed_at: new Date().toISOString(),
              reviewed_by: "当前用户",
              review_comment: "批准充值申请"
            }
          : req
      )
    );
    setShowApprovalDialog(false);
    setSelectedRequest(null);
  };

  // 确认拒绝
  const confirmReject = () => {
    // 这里调用API更新申请状态
    setTopupRequests(prev =>
      prev.map(req =>
        req.id === selectedRequest?.id
          ? {
              ...req,
              status: "rejected",
              reviewed_at: new Date().toISOString(),
              reviewed_by: "当前用户",
              review_comment: reviewComment || "申请被拒绝"
            }
          : req
      )
    );
    setShowRejectionDialog(false);
    setSelectedRequest(null);
    setReviewComment("");
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载财务管理数据中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-8">
      {/* 页面头部 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">财务管理</h1>
          <p className="text-gray-600">充值审批、预算控制、财务分析</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            导出报表
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            充值申请
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">财务概览</TabsTrigger>
          <TabsTrigger value="topup">充值管理</TabsTrigger>
          <TabsTrigger value="analysis">财务分析</TabsTrigger>
          <TabsTrigger value="team">团队预算</TabsTrigger>
        </TabsList>

        {/* 财务概览 */}
        <TabsContent value="overview" className="space-y-6">
          {/* 核心指标 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">账户总余额</CardTitle>
                <Wallet className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">¥{financialSummary.total_balance.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  本月已支出 ¥{financialSummary.this_month_spending.toLocaleString()}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">本月支出</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">¥{financialSummary.this_month_spending.toLocaleString()}</div>
                <p className="text-xs text-green-600 flex items-center">
                  <ArrowUpRight className="w-3 h-3 mr-1" />
                  比上月增长 {((financialSummary.this_month_spending - financialSummary.last_month_spending) / financialSummary.last_month_spending * 100).toFixed(1)}%
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">待审批充值</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">¥{financialSummary.pending_topups.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  {topupRequests.filter(r => r.status === "pending").length} 个申请待审核
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">审批效率</CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{financialSummary.success_rate}%</div>
                <p className="text-xs text-muted-foreground">
                  平均审批时间 {financialSummary.average_approval_time} 小时
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 支出趋势图 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>支出趋势分析</CardTitle>
                <CardDescription>最近7天的支出和充值趋势</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={spendingTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value) => `¥${Number(value).toLocaleString()}`} />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="spending"
                      stackId="1"
                      stroke="#ef4444"
                      fill="#fecaca"
                      name="支出"
                    />
                    <Area
                      type="monotone"
                      dataKey="topups"
                      stackId="2"
                      stroke="#22c55e"
                      fill="#bbf7d0"
                      name="充值"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>平台支出分布</CardTitle>
                <CardDescription>各平台广告支出占比</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={platformSpending}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({platform, percentage}) => `${platform} ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="amount"
                    >
                      {platformSpending.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `¥${Number(value).toLocaleString()}`} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 充值管理 */}
        <TabsContent value="topup" className="space-y-6">
          {/* 筛选和搜索 */}
          <Card>
            <CardHeader>
              <CardTitle>充值申请管理</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="搜索申请人、账户名或申请理由..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="状态筛选" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      <SelectItem value="pending">待审核</SelectItem>
                      <SelectItem value="approved">已批准</SelectItem>
                      <SelectItem value="rejected">已拒绝</SelectItem>
                      <SelectItem value="completed">已完成</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button variant="outline">
                    <Filter className="w-4 h-4 mr-2" />
                    更多筛选
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 申请列表 */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>申请人</TableHead>
                    <TableHead>账户信息</TableHead>
                    <TableHead>申请金额</TableHead>
                    <TableHead>申请理由</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>申请时间</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRequests.map((request) => (
                    <TableRow key={request.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback>{request.user_name[0]}</AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{request.user_name}</div>
                            <div className="text-sm text-gray-500">{request.user_role}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{request.account_name}</div>
                          <div className="text-sm text-gray-500 capitalize">{request.platform}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-semibold">¥{request.amount.toLocaleString()}</div>
                        <div className="text-sm text-gray-500">{request.currency}</div>
                      </TableCell>
                      <TableCell>
                        <div className="max-w-xs truncate" title={request.reason}>
                          {request.reason}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={`flex items-center gap-1 ${getStatusColor(request.status)}`}>
                          {getStatusIcon(request.status)}
                          {getStatusText(request.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {format(new Date(request.created_at), "MM/dd HH:mm", { locale: zhCN })}
                        </div>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>操作</DropdownMenuLabel>
                            <DropdownMenuItem>
                              <Eye className="w-4 h-4 mr-2" />
                              查看详情
                            </DropdownMenuItem>
                            {request.status === "pending" && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => handleApprove(request)}>
                                  <CheckCircle className="w-4 h-4 mr-2" />
                                  批准申请
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleReject(request)}>
                                  <XCircle className="w-4 h-4 mr-2" />
                                  拒绝申请
                                </DropdownMenuItem>
                              </>
                            )}
                            {request.status === "approved" && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem>
                                  <CreditCard className="w-4 h-4 mr-2" />
                                  标记为完成
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 财务分析 */}
        <TabsContent value="analysis" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 支出对比分析 */}
            <Card>
              <CardHeader>
                <CardTitle>月度支出对比</CardTitle>
                <CardDescription>本月与上月支出对比分析</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">本月支出</span>
                    <span className="font-semibold">¥{financialSummary.this_month_spending.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">上月支出</span>
                    <span className="font-semibold">¥{financialSummary.last_month_spending.toLocaleString()}</span>
                  </div>
                  <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{
                        width: `${Math.min((financialSummary.this_month_spending / financialSummary.last_month_spending) * 100, 100)}%`
                      }}
                    />
                  </div>
                  <div className="text-sm text-center text-green-600 font-medium">
                    增长 {((financialSummary.this_month_spending - financialSummary.last_month_spending) / financialSummary.last_month_spending * 100).toFixed(1)}%
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 预算预测 */}
            <Card>
              <CardHeader>
                <CardTitle>预算预测</CardTitle>
                <CardDescription>基于当前趋势的月度预算预测</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">当前已支出</span>
                    <span className="font-semibold">¥{financialSummary.this_month_spending.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">预计总支出</span>
                    <span className="font-semibold">¥{financialSummary.projected_spend.toLocaleString()}</span>
                  </div>
                  <Progress
                    value={(financialSummary.this_month_spending / financialSummary.projected_spend) * 100}
                    className="h-3"
                  />
                  <div className="text-sm text-center text-gray-600">
                    已完成 {((financialSummary.this_month_spending / financialSummary.projected_spend) * 100).toFixed(1)}%
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 平台支出详细分析 */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>平台支出详细分析</CardTitle>
                <CardDescription>各平台支出金额和趋势分析</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={platformSpending}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="platform" />
                    <YAxis />
                    <Tooltip formatter={(value) => `¥${Number(value).toLocaleString()}`} />
                    <Bar dataKey="amount" fill="#3b82f6">
                      {platformSpending.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 团队预算 */}
        <TabsContent value="team" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>团队预算使用情况</CardTitle>
              <CardDescription>各团队成员的预算使用效率和绩效分析</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {teamSpending.map((member) => (
                  <div key={member.user_name} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback>{member.user_name[0]}</AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium">{member.user_name}</div>
                          <div className="text-sm text-gray-500">{member.role}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-semibold">¥{member.total_spent.toLocaleString()}</div>
                        <div className="text-sm text-gray-500">{member.projects_count} 个项目</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>预算利用率</span>
                          <span>{member.budget_utilization}%</span>
                        </div>
                        <Progress value={member.budget_utilization} className="h-2" />
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>效率评分</span>
                          <span>{member.efficiency_score}/100</span>
                        </div>
                        <Progress value={member.efficiency_score} className="h-2" />
                      </div>

                      <div className="flex items-center justify-end gap-2">
                        <Badge variant={member.efficiency_score >= 90 ? "default" : member.efficiency_score >= 80 ? "secondary" : "destructive"}>
                          {member.efficiency_score >= 90 ? "优秀" : member.efficiency_score >= 80 ? "良好" : "需改进"}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 批准申请对话框 */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批准充值申请</DialogTitle>
            <DialogDescription>
              确认批准此充值申请？批准后财务人员将进行充值操作。
            </DialogDescription>
          </DialogHeader>
          {selectedRequest && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>申请人</Label>
                  <div className="font-medium">{selectedRequest.user_name}</div>
                </div>
                <div>
                  <Label>账户</Label>
                  <div className="font-medium">{selectedRequest.account_name}</div>
                </div>
                <div>
                  <Label>申请金额</Label>
                  <div className="font-semibold text-lg">¥{selectedRequest.amount.toLocaleString()}</div>
                </div>
                <div>
                  <Label>申请时间</Label>
                  <div className="font-medium">
                    {format(new Date(selectedRequest.created_at), "yyyy-MM-dd HH:mm")}
                  </div>
                </div>
              </div>
              <div>
                <Label>申请理由</Label>
                <div className="text-sm text-gray-600 mt-1">{selectedRequest.reason}</div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApprovalDialog(false)}>
              取消
            </Button>
            <Button onClick={confirmApprove}>
              确认批准
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 拒绝申请对话框 */}
      <Dialog open={showRejectionDialog} onOpenChange={setShowRejectionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>拒绝充值申请</DialogTitle>
            <DialogDescription>
              请输入拒绝此申请的原因。原因将通知给申请人。
            </DialogDescription>
          </DialogHeader>
          {selectedRequest && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>申请人</Label>
                  <div className="font-medium">{selectedRequest.user_name}</div>
                </div>
                <div>
                  <Label>申请金额</Label>
                  <div className="font-semibold text-lg">¥{selectedRequest.amount.toLocaleString()}</div>
                </div>
              </div>
              <div>
                <Label htmlFor="rejection-reason">拒绝原因 *</Label>
                <textarea
                  id="rejection-reason"
                  className="w-full mt-1 p-3 border rounded-md resize-none"
                  rows={3}
                  placeholder="请输入拒绝原因..."
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectionDialog(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={confirmReject}
              disabled={!reviewComment.trim()}
            >
              确认拒绝
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}