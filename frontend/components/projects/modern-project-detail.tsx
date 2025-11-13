"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Edit,
  DollarSign,
  Users,
  Target,
  TrendingUp,
  Brain,
  Zap,
  AlertTriangle,
  CheckCircle,
  Activity,
  Eye,
  BarChart3,
  Settings,
  Calendar,
  Clock,
  Award,
  Rocket
} from "lucide-react";

interface Project {
  id: number;
  name: string;
  client_name: string;
  status: "planning" | "active" | "paused" | "completed" | "archived";
  priority: "low" | "medium" | "high";
  budget: number;
  current_spend: number;
  progress: number;
  roi: number;
  conversion_rate: number;
  start_date: string;
  end_date: string;
}

interface ModernProjectDetailProps {
  project: Project;
  onBack: () => void;
  onEdit: () => void;
}

const StatusBadge = ({ status }: { status: string }) => {
  const statusConfig = {
    active: { color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30", label: "进行中", icon: <Activity className="w-3 h-3" /> },
    paused: { color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", label: "暂停", icon: <Clock className="w-3 h-3" /> },
    completed: { color: "bg-blue-500/20 text-blue-400 border-blue-500/30", label: "已完成", icon: <CheckCircle className="w-3 h-3" /> },
    planning: { color: "bg-purple-500/20 text-purple-400 border-purple-500/30", label: "规划中", icon: <Target className="w-3 h-3" /> },
    archived: { color: "bg-slate-500/20 text-slate-400 border-slate-500/30", label: "已归档", icon: <Archive className="w-3 h-3" /> }
  };

  const config = statusConfig[status as keyof typeof statusConfig];

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${config.color}`}
    >
      {config.icon}
      <span className="text-xs font-medium">{config.label}</span>
    </motion.div>
  );
};

const MetricCard = ({
  title,
  value,
  icon,
  trend,
  color
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
  color: string;
}) => (
  <motion.div
    whileHover={{ y: -2, boxShadow: "0 10px 30px rgba(0,0,0,0.3)" }}
    className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 backdrop-blur-sm"
  >
    <div className="flex items-center justify-between mb-3">
      <div className={`p-2 rounded-lg bg-gradient-to-br ${color}`}>
        {icon}
      </div>
      {trend && (
        <div className={`flex items-center text-sm ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          <TrendingUp className="w-3 h-3 mr-1" />
          {trend > 0 ? '+' : ''}{trend}%
        </div>
      )}
    </div>
    <p className="text-slate-400 text-xs mb-1">{title}</p>
    <p className="text-xl font-bold text-white">{value}</p>
  </motion.div>
);

export const ModernProjectDetail: React.FC<ModernProjectDetailProps> = ({ project, onBack, onEdit }) => {
  const [activeTab, setActiveTab] = useState("overview");

  const tabs = [
    { id: "overview", label: "概览", icon: <Eye className="w-4 h-4" /> },
    { id: "analytics", label: "分析", icon: <BarChart3 className="w-4 h-4" /> },
    { id: "ai-insights", label: "AI洞察", icon: <Brain className="w-4 h-4" /> },
    { id: "settings", label: "设置", icon: <Settings className="w-4 h-4" /> }
  ];

  const metrics = [
    {
      title: "投资回报率",
      value: `${project.roi.toFixed(2)}x`,
      icon: <TrendingUp className="w-4 h-4 text-white" />,
      trend: 12.5,
      color: "from-emerald-500 to-teal-400"
    },
    {
      title: "转化率",
      value: `${(project.conversion_rate * 100).toFixed(1)}%`,
      icon: <Target className="w-4 h-4 text-white" />,
      trend: -2.3,
      color: "from-blue-500 to-cyan-400"
    },
    {
      title: "预算使用",
      value: `¥${project.current_spend.toLocaleString()}`,
      icon: <DollarSign className="w-4 h-4 text-white" />,
      color: "from-purple-500 to-pink-400"
    },
    {
      title: "项目进度",
      value: `${project.progress}%`,
      icon: <Rocket className="w-4 h-4 text-white" />,
      color: "from-orange-500 to-red-400"
    }
  ];

  return (
    <div className="min-h-screen bg-slate-950">
      {/* 背景装饰 */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-900/10 via-purple-900/10 to-slate-900/50" />
      <div className="fixed top-0 right-0 w-96 h-96 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-full blur-3xl" />

      <div className="relative z-10">
        {/* 顶部导航 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800/50 sticky top-0 z-20"
        >
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={onBack}
                  className="p-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg text-slate-300 hover:text-white transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                </motion.button>

                <div>
                  <h1 className="text-2xl font-bold text-white bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    {project.name}
                  </h1>
                  <p className="text-slate-400 text-sm">{project.client_name}</p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <StatusBadge status={project.status} />

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={onEdit}
                  className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-lg text-white font-medium flex items-center space-x-2 transition-all duration-200"
                >
                  <Edit className="w-4 h-4" />
                  <span>编辑项目</span>
                </motion.button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 主要内容 */}
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* 关键指标卡片 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
          >
            {metrics.map((metric, index) => (
              <MetricCard key={index} {...metric} />
            ))}
          </motion.div>

          {/* 标签页导航 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-8"
          >
            <div className="flex space-x-1 bg-slate-900/50 p-1 rounded-xl border border-slate-800/50">
              {tabs.map((tab) => (
                <motion.button
                  key={tab.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                    activeTab === tab.id
                      ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg"
                      : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                  }`}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </motion.button>
              ))}
            </div>
          </motion.div>

          {/* 标签页内容 */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === "overview" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2 space-y-6">
                    {/* 项目进度 */}
                    <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">项目进度</h3>
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-slate-400">整体进度</span>
                            <span className="text-white font-medium">{project.progress}%</span>
                          </div>
                          <div className="w-full bg-slate-700/50 rounded-full h-2">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${project.progress}%` }}
                              transition={{ duration: 1, delay: 0.5 }}
                              className="h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div className="flex items-center space-x-2">
                            <Calendar className="w-4 h-4 text-slate-400" />
                            <span className="text-slate-400">开始时间:</span>
                            <span className="text-white">{project.start_date}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Calendar className="w-4 h-4 text-slate-400" />
                            <span className="text-slate-400">结束时间:</span>
                            <span className="text-white">{project.end_date}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 性能图表占位 */}
                    <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">性能趋势</h3>
                      <div className="h-64 bg-slate-800/30 rounded-lg flex items-center justify-center">
                        <div className="text-slate-500">图表区域 (需要集成图表库)</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    {/* AI 洞察卡片 */}
                    <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-700/30 rounded-xl p-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <Brain className="w-5 h-5 text-purple-400" />
                        <h3 className="text-lg font-semibold text-white">AI 洞察</h3>
                      </div>

                      <div className="space-y-3">
                        <motion.div
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.6 }}
                          className="p-3 bg-slate-800/50 rounded-lg border-l-4 border-emerald-400"
                        >
                          <div className="flex items-start space-x-2">
                            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="text-sm text-white font-medium">表现优秀</p>
                              <p className="text-xs text-slate-400 mt-1">ROI超出预期28%，建议保持当前投放策略</p>
                            </div>
                          </div>
                        </motion.div>

                        <motion.div
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.7 }}
                          className="p-3 bg-slate-800/50 rounded-lg border-l-4 border-yellow-400"
                        >
                          <div className="flex items-start space-x-2">
                            <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="text-sm text-white font-medium">优化建议</p>
                              <p className="text-xs text-slate-400 mt-1">晚间8-10点转化率较低，建议调整投放时段</p>
                            </div>
                          </div>
                        </motion.div>
                      </div>
                    </div>

                    {/* 快速操作 */}
                    <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">快速操作</h3>
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { icon: <Zap className="w-4 h-4" />, label: "优化投放", color: "from-yellow-500 to-orange-400" },
                          { icon: <BarChart3 className="w-4 h-4" />, label: "查看报表", color: "from-blue-500 to-cyan-400" },
                          { icon: <Users className="w-4 h-4" />, label: "团队协作", color: "from-purple-500 to-pink-400" },
                          { icon: <Award className="w-4 h-4" />, label: "成就勋章", color: "from-emerald-500 to-teal-400" }
                        ].map((action, index) => (
                          <motion.button
                            key={index}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className={`p-3 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg flex flex-col items-center space-y-2 text-slate-300 hover:text-white transition-all duration-200 border border-slate-700/50`}
                          >
                            <div className={`p-2 rounded-lg bg-gradient-to-br ${action.color}`}>
                              {action.icon}
                            </div>
                            <span className="text-xs">{action.label}</span>
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "analytics" && (
                <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-8">
                  <div className="text-center text-slate-400">
                    <BarChart3 className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p>详细分析功能开发中...</p>
                    <p className="text-sm mt-2">将包含转化漏斗、用户画像、渠道分析等功能</p>
                  </div>
                </div>
              )}

              {activeTab === "ai-insights" && (
                <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-8">
                  <div className="text-center text-slate-400">
                    <Brain className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p>AI 深度洞察功能开发中...</p>
                    <p className="text-sm mt-2">将包含智能推荐、异常检测、预测分析等功能</p>
                  </div>
                </div>
              )}

              {activeTab === "settings" && (
                <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-8">
                  <div className="text-center text-slate-400">
                    <Settings className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p>项目设置功能开发中...</p>
                    <p className="text-sm mt-2">将包含预算管理、团队权限、通知设置等功能</p>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};