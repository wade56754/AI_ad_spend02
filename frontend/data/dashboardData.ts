import React from 'react';
import {
  LayoutDashboard,
  FolderKanban,
  CreditCard,
  Users,
  FileText,
  DollarSign,
  BarChart3,
  Target,
  TrendingUp,
  Plus,
  Upload,
  Download,
  AlertTriangle
} from 'lucide-react';

// 模块接口
export interface Module {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  gradient: string;
  href: string;
  stats: {
    active?: number;
    total?: number;
    pending?: number;
    completed?: number;
    reports?: number;
  };
  status: 'active' | 'warning' | 'error';
  trend: number;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  statsLabel: string;
}

// 活动记录接口
export interface Activity {
  id: string;
  type: 'project' | 'account' | 'report' | 'payment' | 'approval';
  title: string;
  description: string;
  timestamp: string;
  status: 'success' | 'warning' | 'error' | 'pending';
  amount?: number;
  user?: string;
}

// 快速操作接口
export interface QuickAction {
  id: string;
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<any>;
  color: string;
}

// 模块数据配置
export const moduleData: Module[] = [
  {
    id: 'projects',
    title: '项目管理',
    description: '管理广告项目、ROI分析、项目生命周期跟踪',
    icon: LayoutDashboard,
    gradient: 'bg-gradient-to-br from-blue-500 to-blue-600',
    href: '/projects',
    stats: { active: 8, total: 12 },
    status: 'active',
    trend: 12.5,
    color: 'primary',
    statsLabel: '个项目'
  },
  {
    id: 'ad-accounts',
    title: '渠道账户',
    description: '管理Facebook广告账户、分配给投手、监控账户状态',
    icon: Users,
    gradient: 'bg-gradient-to-br from-purple-500 to-purple-600',
    href: '/ad-accounts',
    stats: { active: 5, total: 8 },
    status: 'active',
    trend: 8.2,
    color: 'secondary',
    statsLabel: '个账户'
  },
  {
    id: 'daily-reports',
    title: '日报管理',
    description: '投手提交日报、数据员审核、确认粉数和消耗',
    icon: FileText,
    gradient: 'bg-gradient-to-br from-green-500 to-green-600',
    href: '/reports',
    stats: { pending: 12 },
    status: 'warning',
    trend: -3.1,
    color: 'success',
    statsLabel: '个报告'
  },
  {
    id: 'finance',
    title: '财务管理',
    description: '充值申请审批、财务对账、成本分析和预算管理',
    icon: DollarSign,
    gradient: 'bg-gradient-to-br from-yellow-500 to-yellow-600',
    href: '/finance',
    stats: { pending: 3, completed: 15 },
    status: 'warning',
    trend: 5.7,
    color: 'warning',
    statsLabel: '个申请'
  },
  {
    id: 'data-analytics',
    title: '数据统计',
    description: '实时数据监控、转化分析、ROI报表和趋势预测',
    icon: BarChart3,
    gradient: 'bg-gradient-to-br from-pink-500 to-pink-600',
    href: '/analytics',
    stats: { active: 24, total: 30 },
    status: 'active',
    trend: 18.3,
    color: 'info',
    statsLabel: '个报告'
  },
  {
    id: 'campaigns',
    title: '广告投放',
    description: '创建广告活动、管理广告组、设置投放参数和预算',
    icon: Target,
    gradient: 'bg-gradient-to-br from-indigo-500 to-indigo-600',
    href: '/campaigns',
    stats: { active: 15, total: 20 },
    status: 'active',
    trend: -2.4,
    color: 'primary',
    statsLabel: '个活动'
  },
  {
    id: 'ai-monitoring',
    title: 'AI智能监控',
    description: 'AI异常检测、消耗预警、账户寿命预测和智能建议',
    icon: TrendingUp,
    gradient: 'bg-gradient-to-br from-red-500 to-red-600',
    href: '/ai-monitoring',
    stats: { active: 6, total: 8 },
    status: 'error',
    trend: 22.1,
    color: 'error',
    statsLabel: '个监控'
  },
  {
    id: 'settings',
    title: '系统设置',
    description: '用户权限管理、系统参数配置、审计日志查看',
    icon: FolderKanban,
    gradient: 'bg-gradient-to-br from-gray-500 to-gray-600',
    href: '/settings',
    stats: { active: 3, total: 5 },
    status: 'active',
    trend: 0,
    color: 'secondary',
    statsLabel: '个模块'
  }
];

// 活动记录数据配置
export const activityData: Activity[] = [
  {
    id: '1',
    type: 'project',
    title: '新项目创建',
    description: '创建了"美妆品牌Q4推广"项目',
    timestamp: '2025-11-13T10:30:00Z',
    status: 'success',
    user: '张经理'
  },
  {
    id: '2',
    type: 'payment',
    title: '充值申请',
    description: 'Facebook账户充值申请 ￥50,000',
    timestamp: '2025-11-13T09:15:00Z',
    status: 'pending',
    amount: 50000,
    user: '李投手'
  },
  {
    id: '3',
    type: 'report',
    title: '日报提交',
    description: '提交了"服装品牌"项目的日报',
    timestamp: '2025-11-13T08:45:00Z',
    status: 'success',
    user: '王投手'
  },
  {
    id: '4',
    type: 'account',
    title: '账户异常',
    description: '检测到Facebook账户消耗异常增长',
    timestamp: '2025-11-13T07:30:00Z',
    status: 'error',
    user: 'AI监控系统'
  },
  {
    id: '5',
    type: 'approval',
    title: '充值审批',
    description: '审批通过了￥30,000的充值申请',
    timestamp: '2025-11-13T06:15:00Z',
    status: 'success',
    amount: 30000,
    user: '陈财务'
  },
  {
    id: '6',
    type: 'project',
    title: '项目完成',
    description: '"游戏推广Q3"项目已结案',
    timestamp: '2025-11-12T16:30:00Z',
    status: 'success',
    user: '赵经理'
  }
];

// 快速操作数据配置
export const quickActionData: QuickAction[] = [
  {
    id: 'new-project',
    title: '新建项目',
    description: '创建新的广告项目',
    href: '/projects/new',
    icon: Plus,
    color: 'bg-blue-500 hover:bg-blue-600'
  },
  {
    id: 'submit-report',
    title: '提交日报',
    description: '填写今日广告投放数据',
    href: '/reports/new',
    icon: Upload,
    color: 'bg-green-500 hover:bg-green-600'
  },
  {
    id: 'recharge-request',
    title: '充值申请',
    description: '申请广告账户充值',
    href: '/finance/recharge',
    icon: DollarSign,
    color: 'bg-yellow-500 hover:bg-yellow-600'
  },
  {
    id: 'export-report',
    title: '导出报表',
    description: '下载Excel格式报表',
    href: '/analytics/export',
    icon: Download,
    color: 'bg-purple-500 hover:bg-purple-600'
  }
];

// 指标统计数据配置
export const statsData = [
  {
    title: '今日消耗',
    value: '￥12,845',
    change: '+8.2%',
    changeType: 'increase' as const,
    description: '相比昨日增长',
    icon: DollarSign,
    color: 'primary' as const
  },
  {
    title: '活跃项目',
    value: '24',
    change: '+3',
    changeType: 'increase' as const,
    description: '本周新增项目',
    icon: Target,
    color: 'success' as const
  },
  {
    title: 'ROI',
    value: '3.24',
    change: '+0.15',
    changeType: 'increase' as const,
    description: '投资回报率',
    icon: TrendingUp,
    color: 'info' as const
  },
  {
    title: '账户总数',
    value: '156',
    change: '+12',
    changeType: 'increase' as const,
    description: '本月新增账户',
    icon: Users,
    color: 'warning' as const
  },
  {
    title: '待审日报',
    value: '18',
    change: '-5',
    changeType: 'decrease' as const,
    description: '需要审核',
    icon: FileText,
    color: 'error' as const
  },
  {
    title: '转化率',
    value: '2.8%',
    change: '+0.3%',
    changeType: 'increase' as const,
    description: '平均转化率',
    icon: AlertTriangle,
    color: 'success' as const
  }
];

// 系统状态数据配置
export const systemStatusData = [
  {
    name: 'API状态',
    status: '正常',
    type: 'success'
  },
  {
    name: '数据库',
    status: '连接',
    type: 'success'
  },
  {
    name: '响应时间',
    status: '120ms',
    type: 'info'
  },
  {
    name: 'CPU使用率',
    status: '45%',
    type: 'warning'
  }
];