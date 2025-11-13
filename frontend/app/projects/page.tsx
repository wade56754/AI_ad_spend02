"use client";

import React, { useState, useEffect } from "react";
import { PageTemplate } from "@/components/layout/page-template";
import { DataTable } from "@/components/ui/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Plus,
  Search,
  Filter,
  Download,
  RefreshCw,
  Eye,
  Edit,
  Users,
  DollarSign,
  TrendingUp,
  Calendar,
  Target,
  BarChart3,
  Clock,
  CheckCircle,
  AlertTriangle,
  Settings,
  FileText,
  MoreHorizontal,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
  ResponsiveContainer,
} from "recharts";
import { ProjectForm } from "@/components/projects/project-form";
import { ProjectKanban } from "@/components/projects/project-kanban";
import { toast } from "sonner";
import { format, subDays, startOfMonth, endOfMonth } from "date-fns";
import { zhCN } from "date-fns/locale";

// 类型定义
interface Project {
  id: number;
  name: string;
  client_name: string;
  description: string;
  currency: string;
  budget: number;
  current_spend: number;
  status: "planning" | "active" | "paused" | "completed" | "archived";
  priority: "low" | "medium" | "high";
  start_date: string;
  end_date: string;
  progress: number;
  team_lead_id: number;
  team_lead_name: string;
  team_members: number;
  ad_accounts_count: number;
  last_activity: string;
  created_at: string;
  updated_at: string;
  roi: number;
  conversion_rate: number;
  tags: string[];
  documents: Array<{
    name: string;
    url: string;
    upload_time: string;
  }>;
  performance_metrics: {
    total_spend: number;
    total_conversions: number;
    total_follows: number;
    avg_cpl: number;
    avg_cpa: number;
    avg_roas: number;
  };
}

interface ProjectStats {
  total_projects: number;
  active_projects: number;
  total_budget: number;
  total_spend: number;
  avg_roi: number;
  completed_this_month: number;
  at_risk_projects: number;
  upcoming_deadlines: number;
}

// 列定义
const columns = [
  {
    id: "project_info",
    header: "项目信息",
    cell: (row: Project) => (
      <div className="flex flex-col">
        <span className="font-medium">{row.name}</span>
        <span className="text-sm text-gray-500">{row.client_name}</span>
        <div className="flex flex-wrap gap-1 mt-1">
          {row.tags.slice(0, 2).map((tag, index) => (
            <Badge key={index} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
          {row.tags.length > 2 && (
            <Badge variant="outline" className="text-xs">
              +{row.tags.length - 2}
            </Badge>
          )}
        </div>
      </div>
    ),
  },
  {
    id: "status",
    header: "状态",
    cell: (row: Project) => {
      const statusConfig = {
        planning: { icon: Clock, color: "text-blue-600", bg: "bg-blue-100", text: "规划中" },
        active: { icon: CheckCircle, color: "text-green-600", bg: "bg-green-100", text: "进行中" },
        paused: { icon: AlertTriangle, color: "text-yellow-600", bg: "bg-yellow-100", text: "暂停" },
        completed: { icon: CheckCircle, color: "text-purple-600", bg: "bg-purple-100", text: "已完成" },
        archived: { icon: FileText, color: "text-gray-600", bg: "bg-gray-100", text: "已归档" },
      };

      const config = statusConfig[row.status];
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
    id: "priority",
    header: "优先级",
    cell: (row: Project) => {
      const priorityConfig = {
        low: { color: "text-gray-600", bg: "bg-gray-100", text: "低" },
        medium: { color: "text-yellow-600", bg: "bg-yellow-100", text: "中" },
        high: { color: "text-red-600", bg: "bg-red-100", text: "高" },
      };

      const config = priorityConfig[row.priority];

      return (
        <Badge className={config.bg + " " + config.color}>
          {config.text}
        </Badge>
      );
    },
  },
  {
    id: "budget_progress",
    header: "预算进度",
    cell: (row: Project) => {
      const budgetPercentage = (row.current_spend / row.budget) * 100;
      const isOverBudget = budgetPercentage > 100;

      return (
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span>¥{row.current_spend.toLocaleString()}</span>
            <span className="text-gray-500">/ ¥{row.budget.toLocaleString()}</span>
          </div>
          <div className="w-20 bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                isOverBudget ? "bg-red-500" : budgetPercentage > 80 ? "bg-yellow-500" : "bg-green-500"
              }`}
              style={{ width: `${Math.min(budgetPercentage, 100)}%` }}
            />
          </div>
          <div className="text-xs text-gray-500">
            {budgetPercentage.toFixed(1)}%
          </div>
        </div>
      );
    },
  },
  {
    id: "progress",
    header: "项目进度",
    cell: (row: Project) => (
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span>进度</span>
          <span>{row.progress}%</span>
        </div>
        <div className="w-20 bg-gray-200 rounded-full h-2">
          <div
            className="h-2 rounded-full bg-blue-500"
            style={{ width: `${row.progress}%` }}
          />
        </div>
      </div>
    ),
  },
  {
    id: "team",
    header: "团队信息",
    cell: (row: Project) => (
      <div className="flex items-center gap-2">
        <Users className="w-4 h-4 text-gray-400" />
        <span className="text-sm">{row.team_lead_name}</span>
        <Badge variant="outline" className="text-xs">
          {row.team_members}人
        </Badge>
      </div>
    ),
  },
  {
    id: "performance",
    header: "表现指标",
    cell: (row: Project) => (
      <div className="text-sm space-y-1">
        <div className="flex justify-between">
          <span className="text-gray-600">ROI:</span>
          <span className="font-medium text-green-600">{row.roi.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">转化率:</span>
          <span className="font-medium">{(row.conversion_rate * 100).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">账户:</span>
          <span className="font-medium">{row.ad_accounts_count}</span>
        </div>
      </div>
    ),
  },
  {
    id: "timeline",
    header: "时间线",
    cell: (row: Project) => (
      <div className="text-sm space-y-1">
        <div className="flex items-center gap-1 text-gray-600">
          <Calendar className="w-3 h-3" />
          <span>{format(new Date(row.start_date), "MM/dd")}</span>
          <span>-</span>
          <span>{format(new Date(row.end_date), "MM/dd")}</span>
        </div>
        <div className="flex items-center gap-1 text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{format(new Date(row.last_activity), "MM/dd HH:mm")}</span>
        </div>
      </div>
    ),
  },
  {
    id: "actions",
    header: "操作",
    cell: (row: Project) => (
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
          <DropdownMenuItem>
            <Edit className="w-4 h-4 mr-2" />
            编辑项目
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem>
            <BarChart3 className="w-4 h-4 mr-2" />
            查看报表
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Users className="w-4 h-4 mr-2" />
            团队管理
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem className="text-red-600">
            <Settings className="w-4 h-4 mr-2" />
            项目设置
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedPriority, setSelectedPriority] = useState<string>("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showKanban, setShowKanban] = useState(false);
  const [viewMode, setViewMode] = useState<"table" | "kanban">("table");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // 状态选项
  const statusOptions = [
    { value: "all", label: "所有状态" },
    { value: "planning", label: "规划中" },
    { value: "active", label: "进行中" },
    { value: "paused", label: "暂停" },
    { value: "completed", label: "已完成" },
    { value: "archived", label: "已归档" },
  ];

  // 优先级选项
  const priorityOptions = [
    { value: "all", label: "所有优先级" },
    { value: "high", label: "高优先级" },
    { value: "medium", label: "中优先级" },
    { value: "low", label: "低优先级" },
  ];

  // 模拟数据
  const mockProjects: Project[] = [
    {
      id: 1,
      name: "春季推广活动",
      client_name: "ABC科技公司",
      description: "针对新品上市的全方位推广活动",
      currency: "USD",
      budget: 50000,
      current_spend: 32500,
      status: "active",
      priority: "high",
      start_date: "2025-01-01",
      end_date: "2025-03-31",
      progress: 65,
      team_lead_id: 1,
      team_lead_name: "张经理",
      team_members: 5,
      ad_accounts_count: 8,
      last_activity: "2025-01-12T14:30:00Z",
      created_at: "2024-12-15T09:00:00Z",
      updated_at: "2025-01-12T14:30:00Z",
      roi: 3.8,
      conversion_rate: 0.025,
      tags: ["电商", "新品推广", "Q1目标"],
      documents: [
        { name: "项目计划书.pdf", url: "/docs/project-plan.pdf", upload_time: "2024-12-15T09:00:00Z" },
      ],
      performance_metrics: {
        total_spend: 32500,
        total_conversions: 812,
        total_follows: 2150,
        avg_cpl: 15.12,
        avg_cpa: 40.02,
        avg_roas: 3.8,
      },
    },
    {
      id: 2,
      name: "品牌形象提升",
      client_name: "XYZ时尚集团",
      description: "提升品牌知名度和美誉度的长期项目",
      currency: "USD",
      budget: 30000,
      current_spend: 18500,
      status: "active",
      priority: "medium",
      start_date: "2025-01-01",
      end_date: "2025-06-30",
      progress: 42,
      team_lead_id: 2,
      team_lead_name: "李主管",
      team_members: 3,
      ad_accounts_count: 5,
      last_activity: "2025-01-11T16:45:00Z",
      created_at: "2024-12-20T10:30:00Z",
      updated_at: "2025-01-11T16:45:00Z",
      roi: 2.1,
      conversion_rate: 0.018,
      tags: ["品牌建设", "长期项目"],
      documents: [],
      performance_metrics: {
        total_spend: 18500,
        total_conversions: 333,
        total_follows: 890,
        avg_cpl: 20.79,
        avg_cpa: 55.56,
        avg_roas: 2.1,
      },
    },
    {
      id: 3,
      name: "夏季促销活动",
      client_name: "DEF零售连锁",
      description: "夏季清仓促销活动",
      currency: "USD",
      budget: 80000,
      current_spend: 0,
      status: "planning",
      priority: "high",
      start_date: "2025-06-01",
      end_date: "2025-08-31",
      progress: 10,
      team_lead_id: 3,
      team_lead_name: "王总监",
      team_members: 8,
      ad_accounts_count: 12,
      last_activity: "2025-01-10T11:20:00Z",
      created_at: "2025-01-10T09:00:00Z",
      updated_at: "2025-01-10T11:20:00Z",
      roi: 0,
      conversion_rate: 0,
      tags: ["促销活动", "季节性", "夏季"],
      documents: [
        { name: "活动方案.pptx", url: "/docs/summer-promo.pptx", upload_time: "2025-01-10T09:15:00Z" },
      ],
      performance_metrics: {
        total_spend: 0,
        total_conversions: 0,
        total_follows: 0,
        avg_cpl: 0,
        avg_cpa: 0,
        avg_roas: 0,
      },
    },
  ];

  const mockStats: ProjectStats = {
    total_projects: 12,
    active_projects: 8,
    total_budget: 450000,
    total_spend: 185000,
    avg_roi: 2.8,
    completed_this_month: 3,
    at_risk_projects: 2,
    upcoming_deadlines: 4,
  };

  // 获取项目列表
  const fetchProjects = async () => {
    setLoading(true);
    try {
      // const response = await fetch(`/api/v1/projects?page=${currentPage}&size=10`);
      // const result = await response.json();

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800));

      setProjects(mockProjects);
      setTotalCount(mockProjects.length);
      setTotalPages(Math.ceil(mockProjects.length / 10));
    } catch (error) {
      toast.error("获取项目列表失败");
      console.error("获取项目列表错误:", error);
    } finally {
      setLoading(false);
    }
  };

  // 获取统计数据
  const fetchStats = async () => {
    try {
      // const response = await fetch("/api/v1/projects/stats");
      // const result = await response.json();

      setStats(mockStats);
    } catch (error) {
      console.error("获取统计数据错误:", error);
    }
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchProjects();
    fetchStats();
  };

  // 导出项目数据
  const handleExport = async () => {
    try {
      const response = await fetch("/api/v1/projects/export");
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `projects-${format(new Date(), "yyyyMMdd")}.xlsx`;
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

  // 筛选项目
  const filteredProjects = projects.filter(project => {
    const matchesSearch = searchTerm === "" ||
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.client_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus = selectedStatus === "all" || project.status === selectedStatus;
    const matchesPriority = selectedPriority === "all" || project.priority === selectedPriority;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  useEffect(() => {
    fetchProjects();
    fetchStats();
  }, [currentPage]);

  return (
    <PageTemplate
      title="项目管理"
      description="管理所有广告投放项目，跟踪进度和表现"
    >
      <div className="space-y-6">
        {/* 统计卡片 */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">总项目数</p>
                    <p className="text-2xl font-bold">{stats.total_projects}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      进行中: {stats.active_projects}
                    </p>
                  </div>
                  <Target className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">总预算</p>
                    <p className="text-2xl font-bold">¥{stats.total_budget.toLocaleString()}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      已消耗: ¥{stats.total_spend.toLocaleString()}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">平均ROI</p>
                    <p className="text-2xl font-bold text-green-600">{stats.avg_roi.toFixed(2)}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      本月完成: {stats.completed_this_month}
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-200" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">风险项目</p>
                    <p className="text-2xl font-bold text-orange-600">{stats.at_risk_projects}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      即将到期: {stats.upcoming_deadlines}
                    </p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-orange-200" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* 筛选和操作栏 */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* 搜索框 */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="搜索项目名称、客户或标签..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* 筛选器 */}
              <div className="flex flex-wrap gap-2">
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

                <Select value={selectedPriority} onValueChange={setSelectedPriority}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {priorityOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* 视图切换和操作按钮 */}
              <div className="flex gap-2">
                <div className="flex border rounded-lg">
                  <Button
                    variant={viewMode === "table" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("table")}
                    className="rounded-r-none"
                  >
                    列表
                  </Button>
                  <Button
                    variant={viewMode === "kanban" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("kanban")}
                    className="rounded-l-none"
                  >
                    看板
                  </Button>
                </div>
                <Button variant="outline" onClick={handleRefresh}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  刷新
                </Button>
                <Button variant="outline" onClick={handleExport}>
                  <Download className="w-4 h-4 mr-2" />
                  导出
                </Button>
                <Button onClick={() => setShowCreateDialog(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  新建项目
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 项目列表或看板 */}
        {viewMode === "table" ? (
          <Card>
            <CardContent className="p-0">
              <DataTable
                columns={columns}
                data={filteredProjects}
                loading={loading}
                pagination={{
                  currentPage,
                  totalPages,
                  totalCount,
                  onPageChange: setCurrentPage,
                }}
              />
            </CardContent>
          </Card>
        ) : (
          <ProjectKanban projects={filteredProjects} onProjectUpdate={fetchProjects} />
        )}

        {/* 新建项目对话框 */}
        {showCreateDialog && (
          <ProjectForm
            open={showCreateDialog}
            onClose={() => setShowCreateDialog(false)}
            onSubmit={async (data) => {
              try {
                const response = await fetch("/api/v1/projects", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(data),
                });

                if (response.ok) {
                  toast.success("项目创建成功");
                  setShowCreateDialog(false);
                  fetchProjects();
                }
              } catch (error) {
                toast.error("创建失败");
              }
            }}
          />
        )}
      </div>
    </PageTemplate>
  );
}