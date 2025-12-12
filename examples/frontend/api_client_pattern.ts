/**
 * API Client 标准模式 - AI 广告代投系统
 * Version: 1.0
 * SoT Reference: API_SOT.md v9.0, ERROR_CODES_SOT.md v2.1
 *
 * 本文件展示 API 调用的标准写法，供 AI 代码生成参考。
 *
 * 关键模式：
 * 1. 统一的 apiRequest 基础函数
 * 2. 类型安全的响应处理
 * 3. 错误码对齐 ERROR_CODES_SOT.md
 * 4. Token 自动刷新
 * 5. React Query hooks 封装
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// === 基础类型 ===

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  meta?: {
    page?: number;
    page_size?: number;
    total?: number;
  };
}

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// === 基础请求函数 ===

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`;

  // 默认请求头
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // 添加 Token
  const token = getAccessToken();
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    // 401 处理：Token 过期
    if (response.status === 401) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return apiRequest<T>(endpoint, options); // 重试
      }
      clearTokens();
      redirectToLogin();
      throw new ApiError('AUTH_002', 'Token已过期，请重新登录', 401);
    }

    // 非 200 响应处理
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.code || 'API_ERROR',
        errorData.message || `HTTP ${response.status} error`,
        response.status,
        errorData.details
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('SYS_001', '网络请求失败');
  }
}

// === Token 工具函数（简化版） ===

function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

async function refreshAccessToken(): Promise<boolean> {
  // 实现 Token 刷新逻辑
  return false;
}

function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

function redirectToLogin(): void {
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

// === 类型定义 ===

export interface Example {
  id: number;
  name: string;
  status: string;
  amount: number;
  created_at: string;
  updated_at: string | null;
}

export interface ExampleListParams {
  page?: number;
  page_size?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
}

export interface ExampleCreateInput {
  name: string;
  amount: number;
  description?: string;
}

export interface ExampleUpdateInput {
  name?: string;
  description?: string;
}

export interface ExampleStats {
  total: number;
  total_amount: number;
  by_status: Record<string, number>;
}

// === API 函数 ===

export const exampleApi = {
  /**
   * 获取列表
   * GET /api/v1/examples
   */
  list: async (params: ExampleListParams = {}): Promise<ApiResponse<Example[]>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return apiRequest<Example[]>(`/api/v1/examples${query ? `?${query}` : ''}`);
  },

  /**
   * 获取详情
   * GET /api/v1/examples/{id}
   */
  get: async (id: number): Promise<ApiResponse<Example>> => {
    return apiRequest<Example>(`/api/v1/examples/${id}`);
  },

  /**
   * 创建
   * POST /api/v1/examples
   */
  create: async (data: ExampleCreateInput): Promise<ApiResponse<Example>> => {
    return apiRequest<Example>('/api/v1/examples', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * 更新
   * PUT /api/v1/examples/{id}
   */
  update: async (id: number, data: ExampleUpdateInput): Promise<ApiResponse<Example>> => {
    return apiRequest<Example>(`/api/v1/examples/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * 删除
   * DELETE /api/v1/examples/{id}
   */
  delete: async (id: number): Promise<ApiResponse<void>> => {
    return apiRequest<void>(`/api/v1/examples/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * 审批
   * POST /api/v1/examples/{id}/approve
   */
  approve: async (id: number, notes?: string): Promise<ApiResponse<Example>> => {
    return apiRequest<Example>(`/api/v1/examples/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  },

  /**
   * 获取统计数据
   * GET /api/v1/examples/stats
   */
  getStats: async (): Promise<ApiResponse<ExampleStats>> => {
    return apiRequest<ExampleStats>('/api/v1/examples/stats');
  },
};

// === React Query Hooks ===

const QUERY_KEYS = {
  examples: 'examples',
  exampleDetail: (id: number) => ['example', id],
  exampleStats: 'example-stats',
};

/**
 * 获取列表 Hook
 */
export function useExamples(params: ExampleListParams = {}) {
  return useQuery({
    queryKey: [QUERY_KEYS.examples, params],
    queryFn: () => exampleApi.list(params),
    select: (response) => ({
      items: response.data ?? [],
      meta: response.meta,
    }),
  });
}

/**
 * 获取详情 Hook
 */
export function useExample(id: number) {
  return useQuery({
    queryKey: QUERY_KEYS.exampleDetail(id),
    queryFn: () => exampleApi.get(id),
    enabled: id > 0,
    select: (response) => response.data,
  });
}

/**
 * 获取统计 Hook
 */
export function useExampleStats() {
  return useQuery({
    queryKey: [QUERY_KEYS.exampleStats],
    queryFn: () => exampleApi.getStats(),
    select: (response) => response.data,
  });
}

/**
 * 创建 Mutation
 */
export function useCreateExample() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: exampleApi.create,
    onSuccess: () => {
      // 使列表缓存失效
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.examples] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.exampleStats] });
    },
  });
}

/**
 * 更新 Mutation
 */
export function useUpdateExample() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ExampleUpdateInput }) =>
      exampleApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.examples] });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.exampleDetail(variables.id),
      });
    },
  });
}

/**
 * 删除 Mutation
 */
export function useDeleteExample() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: exampleApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.examples] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.exampleStats] });
    },
  });
}

/**
 * 审批 Mutation
 */
export function useApproveExample() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }: { id: number; notes?: string }) =>
      exampleApi.approve(id, notes),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.examples] });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.exampleDetail(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.exampleStats] });
    },
  });
}
