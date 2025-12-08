"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  DollarSign,
  Target,
  Users,
  Brain,
  TrendingUp,
  Activity,
  Eye,
  Zap,
  BarChart3,
  AlertCircle
} from "lucide-react";
import { OptimizedMetricCard } from "./optimized-metric-card";
import { OptimizedButton } from "./optimized-button";
import { useTheme } from "@/hooks/use-theme";

// 数据类型定义
interface DashboardMetrics {
  totalBudget: number;
  activeProjects: number;
  conversionRate: number;
  aiScore: number;
  totalSpend: number;
  roi: number;
  weeklyChange: {
    budget: number;
    projects: number;
    conversion: number;
    aiScore: number;
  };
}

interface RecentProject {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed';
  budget: number;
  spent: number;
  roi: number;
  lastUpdate: string;
}

interface AIInsight {
  id: string;
  type: 'optimization' | 'warning' | 'opportunity';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

export const OptimizedDashboard = () => {
  const { theme } = useTheme();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([]);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 模拟API数据获取
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 模拟数据
        const mockMetrics: DashboardMetrics = {
          totalBudget: 125000,
          activeProjects: 24,
          conversionRate: 3.8,
          aiScore: 92,
          totalSpend: 87450,
          roi: 15.2,
          weeklyChange: {
            budget: 12.5,
            projects: 8.2,
            conversion: -2.1,
            aiScore: 5.8
          }
        };

        const mockProjects: RecentProject[] = [
          {
            id: '1',
            name: 'Facebook广告活动A',
            status: 'running',
            budget: 10000,
            spent: 7800,
            roi: 12.5,
            lastUpdate: '2024-11-13'
          },
          {
            id: '2',
            name: 'Instagram品牌推广',
            status: 'running',
            budget: 5000,
            spent: 4500,
            roi: 8.2,
            lastUpdate: '2024-11-12'
          },
          {
            id: '3',
            name: 'TikTok内容营销',
            status: 'paused',
            budget: 8000,
            spent: 3200,
            roi: 15.8,
            lastUpdate: '2024-11-13'
          }
        ];

        const mockInsights: AIInsight[] = [
          {
            id: '1',
            type: 'optimization',
            title: '投放时段优化建议',
            description: '建议增加晚间投放时段(19:00-22:00)，预计ROI可提升15%',
            priority: 'high'
          },
          {
            id: '2',
            type: 'warning',
            title: '异常流量检测',
            description: '检测到项目#2存在异常点击模式，建议启用防刷保护',
            priority: 'high'
          },
          {
            id: '3',
            type: 'opportunity',
            title: '新渠道机会',
            description: '基于用户画像分析，建议尝试YouTube短视频广告',
            priority: 'medium'
          }
        ];

        setMetrics(mockMetrics);
        setRecentProjects(mockProjects);
        setInsights(mockInsights);
      } catch (err) {
        setError('获取仪表板数据失败');
        console.error('Dashboard data fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // 处理指标卡片点击
  const handleMetricClick = (metricType: string) => {
    console.log(`Clicked on ${metricType} metric`);
    // 这里可以导航到详细页面
  };

  // 获取状态标签样式
  const getStatusBadge = (status: string) => {
    const styles = {
      running: 'bg-green-100 text-green-800 border-green-200',
      paused: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      completed: 'bg-blue-100 text-blue-800 border-blue-200'
    };

    const labels = {
      running: '运行中',
      paused: '已暂停',
      completed: '已完成'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status as keyof typeof styles]}`}>
        {labels[status as keyof typeof labels]}
      </span>
    );
  };

  // 获取洞察类型图标
  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'optimization':
        return <TrendingUp className="w-5 h-5 text-blue-500" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'opportunity':
        return <Zap className="w-5 h-5 text-green-500" />;
      default:
        return <Brain className="w-5 h-5 text-purple-500" />;
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <OptimizedButton onClick={() => window.location.reload()}>
            重新加载
          </OptimizedButton>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" role="main" aria-label="仪表板">
      {/* 页面标题 */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              AI广告代投控制台
            </h1>
            <p className="text-secondary">智能驱动，精准投放</p>
          </div>

          <div className="flex items-center space-x-4">
            <OptimizedButton
              variant="primary"
              icon={<Zap className="w-4 h-4" />}
              onClick={() => console.log('AI分析功能')}
            >
              AI分析
            </OptimizedButton>
          </div>
        </div>
      </motion.header>

      {/* 指标卡片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {loading ? (
          // 加载状态
          Array.from({ length: 4 }).map((_, index) => (
            <OptimizedMetricCard
              key={`loading-${index}`}
              title="加载中"
              value="0"
              icon={<div className="w-6 h-6" />}
              loading={true}
            />
          ))
        ) : (
          metrics && (
            <>
              <OptimizedMetricCard
                title="总预算"
                value={`¥${metrics.totalBudget.toLocaleString()}`}
                change={metrics.weeklyChange.budget}
                changeType={metrics.weeklyChange.budget > 0 ? 'up' : 'down'}
                icon={<DollarSign className="w-6 h-6" />}
                color="primary"
                description="本月广告总预算"
                onClick={() => handleMetricClick('budget')}
              />

              <OptimizedMetricCard
                title="活跃项目"
                value={metrics.activeProjects}
                change={metrics.weeklyChange.projects}
                changeType={metrics.weeklyChange.projects > 0 ? 'up' : 'down'}
                icon={<Target className="w-6 h-6" />}
                color="success"
                description="当前运行中的项目"
                onClick={() => handleMetricClick('projects')}
              />

              <OptimizedMetricCard
                title="转化率"
                value={`${metrics.conversionRate}%`}
                change={metrics.weeklyChange.conversion}
                changeType={metrics.weeklyChange.conversion > 0 ? 'up' : 'down'}
                icon={<Users className="w-6 h-6" />}
                color="warning"
                description="平均转化率百分比"
                onClick={() => handleMetricClick('conversion')}
              />

              <OptimizedMetricCard
                title="AI评分"
                value={metrics.aiScore}
                change={metrics.weeklyChange.aiScore}
                changeType={metrics.weeklyChange.aiScore > 0 ? 'up' : 'down'}
                icon={<Brain className="w-6 h-6" />}
                color="error"
                description="综合性能评分"
                onClick={() => handleMetricClick('ai-score')}
              />
            </>
          )
        )}
      </div>

      {/* 主要内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧内容 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 投放趋势图表 */}
          <motion.section
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="card p-6"
            aria-labelledby="chart-title"
          >
            <h2 id="chart-title" className="text-xl font-semibold mb-4">
              投放趋势
            </h2>
            <div className="h-64 bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <p className="text-secondary">图表组件待集成</p>
                <p className="text-sm text-gray-500 mt-1">建议使用 Chart.js 或 Recharts</p>
              </div>
            </div>
          </motion.section>

          {/* 项目状态列表 */}
          <motion.section
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="card p-6"
            aria-labelledby="projects-title"
          >
            <h2 id="projects-title" className="text-xl font-semibold mb-4">
              项目状态
            </h2>
            <div className="space-y-3" role="list">
              {loading ? (
                // 加载状态
                Array.from({ length: 3 }).map((_, index) => (
                  <div key={`project-loading-${index}`} className="animate-pulse">
                    <div className="flex items-center justify-between p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded"></div>
                        <div className="space-y-2">
                          <div className="w-24 h-4 bg-gray-300 dark:bg-gray-600 rounded"></div>
                          <div className="w-16 h-3 bg-gray-300 dark:bg-gray-600 rounded"></div>
                        </div>
                      </div>
                      <div className="w-16 h-6 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
                    </div>
                  </div>
                ))
              ) : (
                recentProjects.map((project) => (
                  <article
                    key={project.id}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                    role="listitem"
                    tabIndex={0}
                    aria-label={`项目 ${project.name}: ${project.status}`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${
                        project.status === 'running' ? 'bg-green-500 animate-pulse' :
                        project.status === 'paused' ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`} aria-hidden="true" />
                      <div>
                        <h3 className="font-medium">{project.name}</h3>
                        <p className="text-sm text-secondary">
                          ROI: {project.roi}%
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      {getStatusBadge(project.status)}
                    </div>
                  </article>
                ))
              )}
            </div>
          </motion.section>
        </div>

        {/* 右侧内容 */}
        <div className="space-y-6">
          {/* AI洞察 */}
          <motion.section
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="card p-6"
            aria-labelledby="insights-title"
          >
            <h2 id="insights-title" className="text-lg font-semibold mb-4 flex items-center">
              <Brain className="w-5 h-5 mr-2 text-purple-500" />
              AI 洞察
            </h2>
            <div className="space-y-3" role="list">
              {loading ? (
                // 加载状态
                Array.from({ length: 3 }).map((_, index) => (
                  <div key={`insight-loading-${index}`} className="animate-pulse">
                    <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                      <div className="w-32 h-4 bg-gray-300 dark:bg-gray-600 rounded mb-2"></div>
                      <div className="w-48 h-3 bg-gray-300 dark:bg-gray-600 rounded"></div>
                    </div>
                  </div>
                ))
              ) : (
                insights.map((insight) => (
                  <article
                    key={insight.id}
                    className={`p-3 rounded-lg border-l-4 ${
                      insight.type === 'optimization' ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500' :
                      insight.type === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500' :
                      'bg-green-50 dark:bg-green-900/20 border-green-500'
                    }`}
                    role="listitem"
                  >
                    <div className="flex items-start space-x-3">
                      {getInsightIcon(insight.type)}
                      <div className="flex-1">
                        <h3 className="font-medium text-sm mb-1">{insight.title}</h3>
                        <p className="text-xs text-secondary">{insight.description}</p>
                      </div>
                    </div>
                  </article>
                ))
              )}
            </div>
          </motion.section>

          {/* 快速操作 */}
          <motion.section
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
            className="card p-6"
            aria-labelledby="quick-actions-title"
          >
            <h2 id="quick-actions-title" className="text-lg font-semibold mb-4">
              快速操作
            </h2>
            <div className="grid grid-cols-2 gap-3" role="list">
              {[
                { icon: <Target className="w-4 h-4" />, label: "新建项目", action: "create-project" },
                { icon: <Activity className="w-4 h-4" />, label: "查看报表", action: "view-reports" },
                { icon: <Eye className="w-4 h-4" />, label: "实时监控", action: "real-time-monitor" },
                { icon: <Zap className="w-4 h-4" />, label: "优化建议", action: "optimization" }
              ].map((action, index) => (
                <OptimizedButton
                  key={action.action}
                  variant="ghost"
                  onClick={() => console.log(`Quick action: ${action.action}`)}
                  className="flex flex-col items-center space-y-2 p-3 h-auto"
                  aria-label={`快速操作: ${action.label}`}
                >
                  {action.icon}
                  <span className="text-xs">{action.label}</span>
                </OptimizedButton>
              ))}
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
};