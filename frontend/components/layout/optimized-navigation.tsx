"use client";

import React, { useState, useEffect } from "react";
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
  Home,
  TrendingUp,
  Bell,
  User
} from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { OptimizedButton } from "@/components/ui/optimized-button";
import { useTheme } from "@/hooks/use-theme";

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ReactNode;
  color: string;
  badge?: number;
  description?: string;
}

interface NavigationSection {
  category: string;
  items: NavigationItem[];
}

// 导航数据配置
const navigationData: NavigationSection[] = [
  {
    category: "主要功能",
    items: [
      {
        name: "仪表板",
        href: "/",
        icon: <Home className="w-5 h-5" />,
        color: "from-blue-500 to-cyan-400",
        description: "查看总览数据"
      },
      {
        name: "项目管理",
        href: "/projects",
        icon: <Target className="w-5 h-5" />,
        color: "from-purple-500 to-pink-400",
        description: "管理广告项目"
      },
      {
        name: "广告账户",
        href: "/ad-accounts",
        icon: <Users className="w-5 h-5" />,
        color: "from-emerald-500 to-teal-400",
        description: "管理投放账户"
      },
      {
        name: "日报管理",
        href: "/daily-reports",
        icon: <FileText className="w-5 h-5" />,
        color: "from-orange-500 to-red-400",
        description: "提交和审核日报"
      }
    ]
  },
  {
    category: "财务分析",
    items: [
      {
        name: "充值管理",
        href: "/topup",
        icon: <DollarSign className="w-5 h-5" />,
        color: "from-yellow-500 to-orange-400",
        description: "申请充值"
      },
      {
        name: "财务对账",
        href: "/reconciliation",
        icon: <BarChart3 className="w-5 h-5" />,
        color: "from-green-500 to-emerald-400",
        description: "查看对账报告"
      }
    ]
  },
  {
    category: "智能工具",
    items: [
      {
        name: "AI分析",
        href: "/ai-analytics",
        icon: <Brain className="w-5 h-5" />,
        color: "from-purple-500 to-indigo-400",
        description: "AI智能分析"
      },
      {
        name: "性能监控",
        href: "/monitoring",
        icon: <TrendingUp className="w-5 h-5" />,
        color: "from-blue-500 to-purple-400",
        description: "实时性能监控"
      }
    ]
  }
];

interface OptimizedNavigationProps {
  children: React.ReactNode;
}

export const OptimizedNavigation: React.FC<OptimizedNavigationProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const pathname = usePathname();
  const { theme } = useTheme();

  // 响应式处理
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
      if (window.innerWidth >= 1024) {
        setSidebarOpen(false); // 桌面端自动关闭移动端菜单
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 键盘导航支持
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && sidebarOpen && isMobile) {
        setSidebarOpen(false);
      }
    };

    if (sidebarOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [sidebarOpen, isMobile]);

  // 防止背景滚动
  useEffect(() => {
    if (sidebarOpen && isMobile) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [sidebarOpen, isMobile]);

  const NavItem = ({ item }: { item: NavigationItem }) => {
    const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

    return (
      <Link href={item.href}>
        <motion.a
          whileHover={{ x: 4 }}
          whileTap={{ scale: 0.98 }}
          className={`nav-item group relative flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 cursor-pointer ${
            isActive
              ? "active"
              : "text-secondary hover:text-primary hover:bg-surface/50"
          }`}
          role="menuitem"
          aria-current={isActive ? "page" : undefined}
          title={item.description}
        >
          {/* 背景光效 */}
          {isActive && (
            <motion.div
              layoutId="activeTab"
              className={`absolute inset-0 bg-gradient-to-r ${item.color} rounded-xl opacity-10`}
              initial={false}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          )}

          <div className="relative z-10 flex items-center space-x-3 w-full">
            <div className={`p-2 rounded-lg flex-shrink-0 ${
              isActive
                ? "bg-white/20 text-white"
                : "bg-surface/50 text-secondary group-hover:text-primary"
            }`}>
              {item.icon}
            </div>
            <div className="flex-1 min-w-0">
              <span className="font-medium truncate">{item.name}</span>
              {item.description && (
                <p className="text-xs text-tertiary mt-0.5 truncate">{item.description}</p>
              )}
            </div>
            {item.badge && item.badge > 0 && (
              <span className="nav-badge bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full">
                {item.badge > 99 ? "99+" : item.badge}
              </span>
            )}
          </div>

          {/* 悬停效果 */}
          {!isActive && (
            <motion.div
              className={`absolute inset-0 bg-gradient-to-r ${item.color} rounded-xl opacity-0 group-hover:opacity-5 transition-opacity duration-200`}
              aria-hidden="true"
            />
          )}
        </motion.a>
      </Link>
    );
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* 跳过链接 - 可访问性 */}
      <a
        href="#main-content"
        className="skip-link"
        onClick={(e) => {
          e.preventDefault();
          const mainContent = document.getElementById('main-content');
          mainContent?.focus();
        }}
      >
        跳转到主要内容
      </a>

      {/* 移动端遮罩 */}
      <AnimatePresence>
        {sidebarOpen && isMobile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      {/* 侧边栏 */}
      <motion.aside
        initial={false}
        animate={{
          width: isMobile ? (sidebarOpen ? 280 : 0) : 280,
          x: isMobile ? (sidebarOpen ? 0 : -280) : 0
        }}
        className={`nav-sidebar fixed lg:relative flex flex-col z-50 overflow-hidden ${
          isMobile ? 'shadow-2xl' : ''
        }`}
        aria-label="主导航"
      >
        <div className="flex flex-col h-full">
          {/* Logo区域 */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 border-b border-border"
          >
            <Link href="/" className="block" aria-label="AI广告代投系统 - 返回首页">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-primary bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    AI广告代投
                  </h1>
                  <p className="text-xs text-tertiary">智能投放系统</p>
                </div>
              </div>
            </Link>
          </motion.div>

          {/* 导航菜单 */}
          <nav className="flex-1 p-4 space-y-6 overflow-y-auto" role="navigation">
            {navigationData.map((section, sectionIndex) => (
              <motion.div
                key={section.category}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: sectionIndex * 0.1 }}
              >
                <h2 className="text-xs font-medium text-tertiary uppercase tracking-wider mb-3 px-4">
                  {section.category}
                </h2>
                <ul className="space-y-2" role="menu">
                  {section.items.map((item) => (
                    <li key={item.name} role="none">
                      <NavItem item={item} />
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </nav>

          {/* 底部信息 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="p-4 border-t border-border"
          >
            <div className="p-3 bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-700/30 rounded-xl">
              <div className="flex items-center space-x-2 mb-2">
                <Zap className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-primary">AI 助手</span>
              </div>
              <p className="text-xs text-tertiary">需要帮助？随时询问AI助手获取智能建议</p>
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
          className="bg-surface/80 backdrop-blur-md border-b border-border sticky top-0 z-30"
        >
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* 移动端菜单按钮 */}
              <OptimizedButton
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                icon={sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                aria-label={sidebarOpen ? '关闭侧边栏' : '打开侧边栏'}
                aria-expanded={sidebarOpen}
                className="lg:hidden"
              />

              {/* 面包屑导航 */}
              <nav className="hidden md:flex items-center space-x-2 text-sm" aria-label="面包屑导航">
                <span className="text-tertiary">首页</span>
                <span className="text-quaternary" aria-hidden="true">/</span>
                <span className="text-primary font-medium">
                  {pathname === '/' ? '仪表板' :
                   pathname.split('/').pop()?.replace(/-/g, ' ') || '仪表板'}
                </span>
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              {/* 快速操作按钮 */}
              <OptimizedButton
                variant="primary"
                size="sm"
                icon={<Zap className="w-4 h-4" />}
                onClick={() => console.log('快速优化功能')}
                className="hidden md:flex"
              >
                快速优化
              </OptimizedButton>

              {/* 主题切换 */}
              <ThemeToggle />

              {/* 通知按钮 */}
              <OptimizedButton
                variant="ghost"
                size="sm"
                icon={<Bell className="w-5 h-5" />}
                onClick={() => console.log('通知功能')}
                aria-label="查看通知"
                className="relative"
              >
                <span
                  className="absolute top-1 right-1 w-2 h-2 bg-green-500 rounded-full"
                  aria-hidden="true"
                />
                <span className="sr-only">有新通知</span>
              </OptimizedButton>

              {/* 用户头像 */}
              <div className="flex items-center space-x-2">
                <OptimizedButton
                  variant="ghost"
                  size="sm"
                  icon={
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-400 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  }
                  onClick={() => console.log('用户菜单')}
                  aria-label="用户菜单"
                />
              </div>
            </div>
          </div>
        </motion.header>

        {/* 页面内容 */}
        <main
          id="main-content"
          className="flex-1 overflow-auto"
          tabIndex={-1}
          role="main"
        >
          {children}
        </main>
      </div>
    </div>
  );
};