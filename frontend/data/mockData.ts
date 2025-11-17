// Dashboard模拟数据

import { DashboardData } from '@/types/dashboard';

export const mockDashboardData: DashboardData = {
  // KPI数据
  kpis: [
    {
      title: '总消耗',
      value: '￥386,420',
      subtitle: '本月累计',
      color: 'blue',
      trend: {
        value: '12.5%',
        direction: 'up'
      }
    },
    {
      title: '总充值',
      value: '￥520,000',
      subtitle: '本月累计',
      color: 'green',
      trend: {
        value: '8.3%',
        direction: 'up'
      }
    },
    {
      title: '活跃项目',
      value: '24',
      subtitle: '正在进行',
      color: 'orange',
      trend: {
        value: '2个',
        direction: 'up'
      }
    },
    {
      title: '平均ROI',
      value: '18.5%',
      subtitle: '本月表现',
      color: 'purple',
      trend: {
        value: '3.2%',
        direction: 'up'
      }
    }
  ],

  // 趋势数据（最近7天）
  trendData: [
    { date: '2025-01-08', value: 2800 },
    { date: '2025-01-09', value: 3200 },
    { date: '2025-01-10', value: 2900 },
    { date: '2025-01-11', value: 3500 },
    { date: '2025-01-12', value: 3100 },
    { date: '2025-01-13', value: 3800 },
    { date: '2025-01-14', value: 4200 }
  ],

  // 分布数据（用于环形图）
  distributionData: [
    {
      name: 'Facebook',
      value: 185000,
      color: '#3b82f6'
    },
    {
      name: 'Google Ads',
      value: 142000,
      color: '#10b981'
    },
    {
      name: 'TikTok',
      value: 59000,
      color: '#8b5cf6'
    }
  ],

  // 项目数据
  projects: [
    {
      id: '1',
      name: '春季促销活动',
      client: '美妆品牌A',
      manager: '张三',
      status: 'active',
      budget: {
        total: 100000,
        spent: 68500
      },
      roi: 18.5,
      createdAt: '2025-01-10'
    },
    {
      id: '2',
      name: '新品推广',
      client: '科技品牌B',
      manager: '李四',
      status: 'active',
      budget: {
        total: 80000,
        spent: 42000
      },
      roi: 22.3,
      createdAt: '2025-01-08'
    },
    {
      id: '3',
      name: '品牌曝光',
      client: '汽车品牌C',
      manager: '王五',
      status: 'pending',
      budget: {
        total: 120000,
        spent: 0
      },
      roi: 0,
      createdAt: '2025-01-12'
    },
    {
      id: '4',
      name: '电商大促',
      client: '零售品牌D',
      manager: '赵六',
      status: 'active',
      budget: {
        total: 150000,
        spent: 98000
      },
      roi: 15.7,
      createdAt: '2025-01-05'
    },
    {
      id: '5',
      name: '品牌建设',
      client: '餐饮品牌E',
      manager: '孙七',
      status: 'completed',
      budget: {
        total: 60000,
        spent: 60000
      },
      roi: 12.8,
      createdAt: '2024-12-20'
    }
  ]
};