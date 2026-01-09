/**
 * TanStack Query 统一缓存配置
 *
 * 提供标准化的缓存时间和 staleTime 配置
 * 确保全项目一致的缓存策略
 */

/**
 * 缓存时间配置 (毫秒)
 */
export const CACHE_TIME = {
  /** 认证相关数据: 5分钟 */
  AUTH: 5 * 60 * 1000,
  /** 静态/配置数据: 30分钟 */
  STATIC: 30 * 60 * 1000,
  /** 实时数据: 10秒 */
  REALTIME: 10 * 1000,
  /** 默认缓存: 1分钟 */
  DEFAULT: 60 * 1000,
  /** 列表数据: 2分钟 */
  LIST: 2 * 60 * 1000,
  /** 详情数据: 5分钟 */
  DETAIL: 5 * 60 * 1000,
} as const;

/**
 * staleTime 配置 (数据被认为过期的时间)
 */
export const STALE_TIME = {
  /** 认证: 立即过期 (总是重新验证) */
  AUTH: 0,
  /** 静态数据: 10分钟 */
  STATIC: 10 * 60 * 1000,
  /** 实时数据: 0秒 (立即过期) */
  REALTIME: 0,
  /** 默认: 30秒 */
  DEFAULT: 30 * 1000,
  /** 列表: 30秒 */
  LIST: 30 * 1000,
  /** 详情: 1分钟 */
  DETAIL: 60 * 1000,
} as const;

/**
 * 获取标准 Query 配置
 */
export function getQueryConfig(type: keyof typeof CACHE_TIME = 'DEFAULT') {
  return {
    staleTime: STALE_TIME[type],
    gcTime: CACHE_TIME[type], // TanStack Query v5 使用 gcTime 替代 cacheTime
    refetchOnWindowFocus: type === 'REALTIME',
    refetchOnReconnect: true,
    retry: type === 'AUTH' ? 1 : 3,
  };
}

/**
 * Query Key 工厂函数
 * 提供类型安全的 Query Key 生成
 */
export const queryKeys = {
  // 认证
  auth: {
    all: ['auth'] as const,
    user: () => [...queryKeys.auth.all, 'user'] as const,
    session: () => [...queryKeys.auth.all, 'session'] as const,
  },
  // 充值
  topups: {
    all: ['topups'] as const,
    list: (params?: Record<string, unknown>) => [...queryKeys.topups.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.topups.all, 'detail', id] as const,
    stats: () => [...queryKeys.topups.all, 'stats'] as const,
  },
  // 日报
  dailyReports: {
    all: ['dailyReports'] as const,
    list: (params?: Record<string, unknown>) => [...queryKeys.dailyReports.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.dailyReports.all, 'detail', id] as const,
    dashboard: () => [...queryKeys.dailyReports.all, 'dashboard'] as const,
  },
  // 广告账户
  adAccounts: {
    all: ['adAccounts'] as const,
    list: (params?: Record<string, unknown>) => [...queryKeys.adAccounts.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.adAccounts.all, 'detail', id] as const,
  },
  // 项目
  projects: {
    all: ['projects'] as const,
    list: (params?: Record<string, unknown>) => [...queryKeys.projects.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.projects.all, 'detail', id] as const,
  },
  // 供应商
  suppliers: {
    all: ['suppliers'] as const,
    list: (params?: Record<string, unknown>) => [...queryKeys.suppliers.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.suppliers.all, 'detail', id] as const,
  },
  // 结算
  settlements: {
    all: ['settlements'] as const,
    list: (params?: Record<string, unknown>) => [...queryKeys.settlements.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.settlements.all, 'detail', id] as const,
  },
  // 对账
  reconciliation: {
    all: ['reconciliation'] as const,
    batches: (params?: Record<string, unknown>) => [...queryKeys.reconciliation.all, 'batches', params] as const,
    details: (batchId: string) => [...queryKeys.reconciliation.all, 'details', batchId] as const,
  },
  // 仪表盘
  dashboard: {
    all: ['dashboard'] as const,
    stats: () => [...queryKeys.dashboard.all, 'stats'] as const,
    trends: (dateRange?: string) => [...queryKeys.dashboard.all, 'trends', dateRange] as const,
  },
} as const;

export type QueryKeys = typeof queryKeys;
