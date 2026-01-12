/**
 * 应用常量定义
 * @module lib/constants
 */

// API 配置
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 分页默认值
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;

// 日期格式
export const DATE_FORMAT = 'yyyy-MM-dd';
export const DATETIME_FORMAT = 'yyyy-MM-dd HH:mm:ss';
export const TIME_FORMAT = 'HH:mm:ss';

// 货币
export const CURRENCY_SYMBOL = '¥';
export const CURRENCY_LOCALE = 'zh-CN';
export const CURRENCY_CODE = 'CNY';

// 状态颜色映射
export const STATUS_COLORS = {
  // 日报状态
  raw_submitted: 'bg-gray-100 text-gray-800',
  trend_pending: 'bg-yellow-100 text-yellow-800',
  trend_ok: 'bg-green-100 text-green-800',
  trend_flagged: 'bg-red-100 text-red-800',
  trend_resolved: 'bg-blue-100 text-blue-800',
  final_pending: 'bg-orange-100 text-orange-800',
  final_confirmed: 'bg-emerald-100 text-emerald-800',
  final_locked: 'bg-purple-100 text-purple-800',

  // 通用状态
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-800',
  pending: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-blue-100 text-blue-800',
  failed: 'bg-red-100 text-red-800',
} as const;

// 状态中文名称
export const STATUS_LABELS = {
  // 日报状态
  raw_submitted: '已提交',
  trend_pending: '趋势待审',
  trend_ok: '趋势通过',
  trend_flagged: '趋势异常',
  trend_resolved: '异常已解决',
  final_pending: '终审待审',
  final_confirmed: '终审通过',
  final_locked: '已锁定',

  // 通用状态
  active: '激活',
  inactive: '未激活',
  pending: '待处理',
  completed: '已完成',
  failed: '失败',
} as const;

// 路由路径
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  PROJECTS: '/projects',
  DAILY_REPORTS: '/daily-reports',
  RECONCILIATION: '/reconciliation',
  TOPUPS: '/topups',
  LEDGER: '/ledger',
  FINANCE_PROFIT: '/finance/profit',
  SETTINGS: '/settings',
  REPORTS: '/reports',
  AD_ACCOUNTS: '/ad-accounts',
  CHANNELS: '/channels',
  SUPPLIERS: '/suppliers',
  SETTLEMENTS: '/settlements',
  TRANSFERS: '/transfers',
  IMPORT_JOBS: '/import-jobs',
} as const;

// 本地存储键
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  THEME: 'theme',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
} as const;
