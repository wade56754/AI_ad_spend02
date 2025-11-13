"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Target,
  DollarSign,
  Users,
  FileText,
  Settings,
  Brain,
  Zap,
  Menu,
  X,
  ChevronDown,
  Home,
  TrendingUp,
  Shield,
  Bell
} from "lucide-react";

const navigationItems = [
  {
    category: "主要功能",
    items: [
      { name: "仪表板", href: "/dashboard", icon: <Home className="w-5 h-5" />, color: "from-blue-500 to-cyan-400" },
      { name: "项目管理", href: "/projects", icon: <Target className="w-5 h-5" />, color: "from-purple-500 to-pink-400" },
      { name: "广告账户", href: "/ad-accounts", icon: <Users className="w-5 h-5" />, color: "from-emerald-500 to-teal-400" },
      { name: "日报管理", href: "/daily-reports", icon: <FileText className="w-5 h-5" />, color: "from-orange-500 to-red-400" }
    ]
  },
  {
    category: "财务分析",
    items: [
      { name: "充值管理", href: "/topup", icon: <DollarSign className="w-5 h-5" />, color: "from-yellow-500 to-orange-400" },
      { name: "财务对账", href: "/reconciliation", icon: <BarChart3 className="w-5 h-5" />, color: "from-green-500 to-emerald-400" }
    ]
  },
  {
    category: "智能工具",
    items: [
      { name: "AI分析", href: "/ai-analytics", icon: <Brain className="w-5 h-5" />, color: "from-purple-500 to-indigo-400" },
      { name: "性能监控", href: "/monitoring", icon: <TrendingUp className="w-5 h-5" />, color: "from-blue-500 to-purple-400" }
    ]
  }
];

interface ModernNavigationProps {
  children: React.ReactNode;
}

export const ModernNavigation: React.FC<ModernNavigationProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  const NavItem = ({ item }: { item: any }) => {
    const isActive = pathname === item.href || pathname.startsWith(item.href + "/");

    return (
      <Link href={item.href}>
        <motion.div
          whileHover={{ x: 4 }}
          whileTap={{ scale: 0.98 }}
          className={`relative group flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 cursor-pointer ${
            isActive
              ? "bg-gradient-to-r " + item.color + " text-white shadow-lg"
              : "text-slate-400 hover:text-white hover:bg-slate-800/50"
          }`}
        >
          {/* 背景光效 */}
          {isActive && (
            <motion.div
              layoutId="activeTab"
              className={`absolute inset-0 bg-gradient-to-r ${item.color} rounded-xl opacity-20`}
              initial={false}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          )}

          <div className={`relative z-10 flex items-center space-x-3`}>
            <div className={`p-2 rounded-lg ${isActive ? "bg-white/20" : "bg-slate-700/50"}`}>
              {item.icon}
            </div>
            <span className="font-medium">{item.name}</span>
          </div>

          {/* 悬停效果 */}
          {!isActive && (
            <motion.div
              className={`absolute inset-0 bg-gradient-to-r ${item.color} rounded-xl opacity-0 group-hover:opacity-10 transition-opacity duration-200`}
            />
          )}
        </motion.div>
      </Link>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 flex">
      {/* 移动端遮罩 */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* 侧边栏 */}
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 280 : 0 }}
        className={`fixed lg:relative lg:flex flex-col bg-slate-900/95 backdrop-blur-xl border-r border-slate-800/50 z-50 overflow-hidden ${
          sidebarOpen ? "w-280" : "w-0 lg:w-64"
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo区域 */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 border-b border-slate-800/50"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  AI广告代投
                </h1>
                <p className="text-xs text-slate-400">智能投放系统</p>
              </div>
            </div>
          </motion.div>

          {/* 导航菜单 */}
          <nav className="flex-1 p-4 space-y-6 overflow-y-auto">
            {navigationItems.map((section, sectionIndex) => (
              <motion.div
                key={section.category}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: sectionIndex * 0.1 }}
              >
                <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3 px-4">
                  {section.category}
                </h3>
                <div className="space-y-2">
                  {section.items.map((item, itemIndex) => (
                    <NavItem key={item.name} item={item} />
                  ))}
                </div>
              </motion.div>
            ))}
          </nav>

          {/* 底部信息 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="p-4 border-t border-slate-800/50"
          >
            <div className="p-3 bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-700/30 rounded-xl">
              <div className="flex items-center space-x-2 mb-2">
                <Zap className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-white">AI 助手</span>
              </div>
              <p className="text-xs text-slate-400">需要帮助？随时询问AI助手获取智能建议</p>
            </div>
          </motion.div>
        </div>
      </motion.aside>

      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* 顶部导航栏 */}
        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800/50 sticky top-0 z-30"
        >
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* 移动端菜单按钮 */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg text-slate-300 hover:text-white transition-colors"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>

              {/* 面包屑导航 */}
              <nav className="hidden md:flex items-center space-x-2 text-sm">
                <span className="text-slate-400">首页</span>
                <span className="text-slate-600">/</span>
                <span className="text-white">{pathname.split('/').pop() || '仪表板'}</span>
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              {/* 快速操作按钮 */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="hidden md:flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-lg text-white font-medium transition-all duration-200"
              >
                <Zap className="w-4 h-4" />
                <span>快速优化</span>
              </motion.button>

              {/* 通知按钮 */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="relative p-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg text-slate-300 hover:text-white transition-colors"
              >
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-emerald-400 rounded-full" />
              </motion.button>

              {/* 用户头像 */}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-400 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">A</span>
                </div>
                <ChevronDown className="w-4 h-4 text-slate-400" />
              </div>
            </div>
          </div>
        </motion.header>

        {/* 页面内容 */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};