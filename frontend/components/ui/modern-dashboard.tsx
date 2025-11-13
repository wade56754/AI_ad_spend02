"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Users,
  DollarSign,
  Target,
  Activity,
  Zap,
  Eye,
  Brain
} from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  gradient: string;
  delay?: number;
}

const MetricCard = ({ title, value, change, icon, gradient, delay = 0 }: MetricCardProps) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.5 }}
    className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-6 border border-slate-700/50 hover:border-slate-600 transition-all duration-300 group"
  >
    {/* 背景光效 */}
    <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-10 group-hover:opacity-20 transition-opacity duration-300`} />

    <div className="relative z-10">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-lg`}>
          {icon}
        </div>
        {change && (
          <div className={`flex items-center text-sm font-medium ${
            change > 0 ? 'text-emerald-400' : 'text-red-400'
          }`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            {Math.abs(change)}%
          </div>
        )}
      </div>

      <div>
        <p className="text-slate-400 text-sm mb-1">{title}</p>
        <p className="text-2xl font-bold text-white">{value}</p>
      </div>
    </div>

    {/* 装饰性元素 */}
    <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-gradient-to-br from-white/5 to-transparent rounded-full blur-xl" />
  </motion.div>
);

export const ModernDashboard = () => {
  const metrics = [
    {
      title: "总消耗",
      value: "¥328,450",
      change: 12.5,
      icon: <DollarSign className="w-6 h-6 text-white" />,
      gradient: "from-blue-500 to-cyan-400"
    },
    {
      title: "活跃项目",
      value: 24,
      change: 8.2,
      icon: <Target className="w-6 h-6 text-white" />,
      gradient: "from-purple-500 to-pink-400"
    },
    {
      title: "转化率",
      value: "3.24%",
      change: -2.1,
      icon: <Users className="w-6 h-6 text-white" />,
      gradient: "from-emerald-500 to-teal-400"
    },
    {
      title: "AI评分",
      value: 92,
      change: 5.8,
      icon: <Brain className="w-6 h-6 text-white" />,
      gradient: "from-orange-500 to-red-400"
    }
  ];

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      {/* 顶部标题区域 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              AI广告代投控制台
            </h1>
            <p className="text-slate-400">智能驱动，精准投放</p>
          </div>

          <div className="flex items-center space-x-4">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg text-white font-medium flex items-center space-x-2 cursor-pointer"
            >
              <Zap className="w-4 h-4" />
              <span>AI分析</span>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* 指标卡片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} delay={index * 0.1} />
        ))}
      </div>

      {/* 主要内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧图表区域 */}
        <div className="lg:col-span-2 space-y-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-slate-900/50 border border-slate-700/50 rounded-2xl p-6"
          >
            <h3 className="text-xl font-semibold text-white mb-4">投放趋势</h3>
            <div className="h-64 bg-slate-800/50 rounded-xl flex items-center justify-center">
              <div className="text-slate-500">图表区域</div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-slate-900/50 border border-slate-700/50 rounded-2xl p-6"
          >
            <h3 className="text-xl font-semibold text-white mb-4">项目状态</h3>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                    <span className="text-white">项目 #{i}</span>
                  </div>
                  <span className="text-slate-400 text-sm">运行中</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* 右侧信息区域 */}
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-700/30 rounded-2xl p-6"
          >
            <div className="flex items-center space-x-2 mb-4">
              <Brain className="w-5 h-5 text-purple-400" />
              <h3 className="text-lg font-semibold text-white">AI 洞察</h3>
            </div>
            <div className="space-y-3">
              <div className="p-3 bg-slate-800/50 rounded-lg border-l-4 border-purple-400">
                <p className="text-sm text-slate-300">建议增加晚间投放时段，ROI可提升15%</p>
              </div>
              <div className="p-3 bg-slate-800/50 rounded-lg border-l-4 border-blue-400">
                <p className="text-sm text-slate-300">检测到异常点击模式，建议启用防刷保护</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-slate-900/50 border border-slate-700/50 rounded-2xl p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">快速操作</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { icon: <Target className="w-4 h-4" />, label: "新建项目" },
                { icon: <Activity className="w-4 h-4" />, label: "查看报表" },
                { icon: <Eye className="w-4 h-4" />, label: "实时监控" },
                { icon: <Zap className="w-4 h-4" />, label: "优化建议" }
              ].map((action, index) => (
                <motion.button
                  key={index}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-3 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg flex flex-col items-center space-y-2 text-slate-300 hover:text-white transition-all duration-200"
                >
                  {action.icon}
                  <span className="text-xs">{action.label}</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};