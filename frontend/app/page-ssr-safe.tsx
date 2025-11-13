"use client";

/**
 * 黄金规则13：必须延迟渲染动态内容
 *
 * 这个页面演示了如何正确处理SSR水合问题
 * 确保服务器和客户端的首次渲染100%一致
 */

import React, { useState, useEffect } from 'react';
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
  AlertCircle,
  Menu,
  X,
  Bell,
  User,
  Home
} from "lucide-react";

// 黄金规则13实现：安全的客户端环境检测
const useIsMounted = () => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    // 确保只在客户端执行
    setIsMounted(true);
  }, []);

  return isMounted;
};

// 安全的主题Hook - 防止SSR闪烁
const useThemeSafe = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const isMounted = useIsMounted();

  useEffect(() => {
    if (!isMounted) return;

    // 从localStorage读取保存的主题（仅在客户端）
    try {
      const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
      if (savedTheme) {
        setTheme(savedTheme);
      } else {
        // 检查系统主题偏好
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
      }
    } catch (error) {
      console.warn('主题读取失败:', error);
    }
  }, [isMounted]);

  useEffect(() => {
    if (!isMounted) return;

    // 应用主题到DOM（仅在客户端）
    document.documentElement.setAttribute('data-theme', theme);

    // 保存到localStorage（仅在客户端）
    try {
      localStorage.setItem('theme', theme);
    } catch (error) {
      console.warn('主题保存失败:', error);
    }
  }, [theme, isMounted]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return { theme, toggleTheme, isMounted };
};

// 安全的异步数据Hook
const useAsyncData = <T>(
  asyncFn: () => Promise<T>,
  deps: React.DependencyList = []
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const isMounted = useIsMounted();

  useEffect(() => {
    if (!isMounted) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await asyncFn();
        if (isMounted) {
          setData(result);
        }
      } catch (err) {
        if (isMounted) {
          setError(err as Error);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();
  }, deps);

  return { data, loading, error, isMounted };
};

// 安全的指标卡片组件
const MetricCard = ({ title, value, change, changeType, icon, color, loading, description, onClick }: any) => {
  const [isHovered, setIsHovered] = useState(false);

  // 黄金规则13：服务器端只渲染静态内容
  if (loading) {
    return (
      <div className="animate-pulse bg-gray-800 p-6 rounded-xl border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="w-8 h-8 bg-gray-600 rounded-lg"></div>
          <div className="w-16 h-4 bg-gray-600 rounded"></div>
        </div>
        <div className="w-24 h-8 bg-gray-600 rounded mb-2"></div>
        <div className="w-32 h-4 bg-gray-600 rounded"></div>
      </div>
    );
  }

  const colorClasses = {
    primary: 'bg-gradient-to-br from-blue-500 to-blue-600',
    success: 'bg-gradient-to-br from-green-500 to-green-600',
    warning: 'bg-gradient-to-br from-yellow-500 to-yellow-600',
    error: 'bg-gradient-to-br from-red-500 to-red-600',
  };

  const formatNumber = (num: string | number): string => {
    const n = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(n)) return '0';
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toFixed(0);
  };

  return (
    <div
      className={`${colorClasses[color]} p-6 rounded-xl text-white cursor-pointer transform transition-all duration-300 ${isHovered ? 'scale-105 -translate-y-1' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 bg-white/20 rounded-lg">
          {icon}
        </div>
        {change && (
          <div className={`flex items-center text-sm font-medium ${
            changeType === 'up' ? 'text-green-300' : 'text-red-300'
          }`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="space-y-1">
        <h3 className="text-2xl font-bold">{formatNumber(value)}</h3>
        <p className="text-sm opacity-90">{title}</p>
        {description && (
          <p className="text-xs opacity-75 mt-2">{description}</p>
        )}
      </div>
    </div>
  );
};

// 安全的导航组件
const Navigation = ({ children }: { children: React.ReactNode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme, isMounted } = useThemeSafe();

  // 黄金规则13：客户端挂载前不渲染动态内容
  const navigationItems = [
    { name: "仪表板", href: "/", icon: <Home className="w-5 h-5" /> },
    { name: "项目管理", href: "/projects", icon: <Target className="w-5 h-5" /> },
    { name: "广告账户", href: "/ad-accounts", icon: <Users className="w-5 h-5" /> },
    { name: "日报管理", href: "/daily-reports", icon: <Eye className="w-5 h-5" /> },
  ];

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* 侧边栏 */}
      <div className={`fixed lg:relative bg-gray-800 border-r border-gray-700 h-screen transition-transform duration-300 z-50 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} w-64`}>
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">AI广告代投</h1>
              <p className="text-xs text-gray-400">智能投放系统</p>
            </div>
          </div>
        </div>

        <nav className="p-4">
          {navigationItems.map((item) => (
            <a
              key={item.name}
              href={item.href}
              className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:text-white hover:bg-gray-700 transition-colors mb-2"
            >
              {item.icon}
              <span>{item.name}</span>
            </a>
          ))}
        </nav>
      </div>

      {/* 移动端遮罩 */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col">
        {/* 顶部导航栏 */}
        <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 bg-gray-700 rounded-lg text-gray-300 hover:text-white"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              <nav className="hidden md:flex items-center space-x-2 text-sm">
                <span className="text-gray-400">首页</span>
                <span className="text-gray-600">/</span>
                <span className="text-white">仪表板</span>
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => window.location.href = 'http://localhost:8001/docs'}
                className="hidden md:flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-colors"
              >
                <Zap className="w-4 h-4" />
                <span>API文档</span>
              </button>

              {/* 黄金规则13：主题切换按钮只在客户端渲染 */}
              {isMounted && (
                <button
                  onClick={toggleTheme}
                  className="p-2 bg-gray-700 rounded-lg text-gray-300 hover:text-white"
                  title={`切换到${theme === 'dark' ? '浅色' : '深色'}主题`}
                >
                  {theme === 'dark' ? '☀️' : '🌙'}
                </button>
              )}

              <button className="relative p-2 bg-gray-700 rounded-lg text-gray-300 hover:text-white">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-green-500 rounded-full"></span>
              </button>

              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-400 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
            </div>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
};

export default function SSRSafeHomePage() {
  // 黄金规则13：使用安全的异步数据Hook
  const { data: metrics, loading, error } = useAsyncData(async () => {
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 1000));

    return {
      totalBudget: 125000,
      activeProjects: 24,
      conversionRate: 3.8,
      aiScore: 92,
      weeklyChange: {
        budget: 12.5,
        projects: 8.2,
        conversion: -2.1,
        aiScore: 5.8
      }
    };
  }, []);

  // 错误状态
  if (error) {
    return (
      <Navigation>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600 mb-4">数据加载失败</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg text-white"
            >
              重新加载
            </button>
          </div>
        </div>
      </Navigation>
    );
  }

  return (
    <Navigation>
      <div className="p-6">
        {/* SSR安全说明 */}
        <div className="mb-8 p-4 bg-blue-900/20 border border-blue-700/30 rounded-xl">
          <h3 className="text-lg font-semibold text-blue-400 mb-2">🛡️ SSR安全模式</h3>
          <p className="text-sm text-gray-300 mb-2">
            本页面遵循"黄金规则13：必须延迟渲染动态内容"
          </p>
          <ul className="text-xs text-gray-400 space-y-1">
            <li>✅ 服务器和客户端首次渲染100%一致</li>
            <li>✅ 客户端环境检测延迟到水合之后</li>
            <li>✅ 主题切换只在客户端执行</li>
            <li>✅ 动态数据异步加载</li>
          </ul>
        </div>

        {/* 页面标题 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                AI广告代投控制台 (SSR安全版)
              </h1>
              <p className="text-gray-400">智能驱动，精准投放 - 无水合问题</p>
            </div>

            <div className="flex items-center space-x-4">
              <button className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg text-white font-medium hover:from-blue-600 hover:to-purple-600 transition-all">
                <Zap className="w-4 h-4" />
                <span>AI分析</span>
              </button>
            </div>
          </div>
        </div>

        {/* 指标卡片网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {loading ? (
            // 加载状态 - 服务器端和客户端初始渲染一致
            Array.from({ length: 4 }).map((_, index) => (
              <MetricCard
                key={`loading-${index}`}
                title="加载中"
                value="0"
                icon={<div className="w-6 h-6" />}
                loading={true}
                color="primary"
              />
            ))
          ) : (
            metrics && (
              <>
                <MetricCard
                  title="总预算"
                  value={`¥${metrics.totalBudget.toLocaleString()}`}
                  change={metrics.weeklyChange.budget}
                  changeType={metrics.weeklyChange.budget > 0 ? 'up' : 'down'}
                  icon={<DollarSign className="w-6 h-6" />}
                  color="primary"
                  description="本月广告总预算"
                />

                <MetricCard
                  title="活跃项目"
                  value={metrics.activeProjects}
                  change={metrics.weeklyChange.projects}
                  changeType={metrics.weeklyChange.projects > 0 ? 'up' : 'down'}
                  icon={<Target className="w-6 h-6" />}
                  color="success"
                  description="当前运行中的项目"
                />

                <MetricCard
                  title="转化率"
                  value={`${metrics.conversionRate}%`}
                  change={metrics.weeklyChange.conversion}
                  changeType={metrics.weeklyChange.conversion > 0 ? 'up' : 'down'}
                  icon={<Users className="w-6 h-6" />}
                  color="warning"
                  description="平均转化率百分比"
                />

                <MetricCard
                  title="AI评分"
                  value={metrics.aiScore}
                  change={metrics.weeklyChange.aiScore}
                  changeType={metrics.weeklyChange.aiScore > 0 ? 'up' : 'down'}
                  icon={<Brain className="w-6 h-6" />}
                  color="error"
                  description="综合性能评分"
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
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
              <h3 className="text-xl font-semibold text-white mb-4">投放趋势</h3>
              <div className="h-64 bg-gray-700 rounded-xl flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="w-12 h-12 text-gray-500 mx-auto mb-2" />
                  <p className="text-gray-400">图表组件待集成</p>
                  <p className="text-sm text-gray-500 mt-1">建议使用 Chart.js 或 Recharts</p>
                </div>
              </div>
            </div>

            {/* 项目状态列表 */}
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
              <h3 className="text-xl font-semibold text-white mb-4">项目状态</h3>
              <div className="space-y-3">
                {[
                  { name: "Facebook广告活动A", status: "运行中", roi: 12.5 },
                  { name: "Instagram品牌推广", status: "运行中", roi: 8.2 },
                  { name: "TikTok内容营销", status: "已暂停", roi: 15.8 }
                ].map((project, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${
                        project.status === '运行中' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
                      }`} />
                      <span className="text-white">{project.name}</span>
                    </div>
                    <div className="text-right">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                        project.status === '运行中'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {project.status}
                      </span>
                      <p className="text-xs text-gray-400 mt-1">ROI: {project.roi}%</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 右侧内容 */}
          <div className="space-y-6">
            {/* SSR安全提示 */}
            <div className="bg-gradient-to-br from-green-900/20 to-blue-900/20 border border-green-700/30 rounded-xl p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Brain className="w-5 h-5 text-green-400" />
                <h3 className="text-lg font-semibold text-white">SSR安全保障</h3>
              </div>
              <div className="space-y-3">
                <div className="p-3 bg-gray-800/50 rounded-lg border-l-4 border-green-400">
                  <p className="text-sm text-gray-300">✅ 无水合失败警告</p>
                </div>
                <div className="p-3 bg-gray-800/50 rounded-lg border-l-4 border-blue-400">
                  <p className="text-sm text-gray-300">✅ 服务器客户端渲染一致</p>
                </div>
              </div>
            </div>

            {/* 快速操作 */}
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">快速操作</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { icon: <Target className="w-4 h-4" />, label: "新建项目" },
                  { icon: <Activity className="w-4 h-4" />, label: "查看报表" },
                  { icon: <Eye className="w-4 h-4" />, label: "实时监控" },
                  { icon: <Zap className="w-4 h-4" />, label: "优化建议" }
                ].map((action, index) => (
                  <button
                    key={index}
                    className="p-3 bg-gray-700 hover:bg-gray-600 rounded-lg flex flex-col items-center space-y-2 text-gray-300 hover:text-white transition-all"
                  >
                    {action.icon}
                    <span className="text-xs">{action.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 服务状态 */}
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">服务状态</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">前端服务</span>
                  <span className="text-green-400 text-sm">✅ 运行中</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">后端API</span>
                  <span className="text-green-400 text-sm">✅ 运行中</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">SSR安全</span>
                  <span className="text-green-400 text-sm">✅ 已启用</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Navigation>
  );
}