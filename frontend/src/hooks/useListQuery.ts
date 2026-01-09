'use client';

/**
 * 通用列表查询 Hook
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §8 (API 调用规范)
 * - PROMPT_LIBRARY_FRONTEND.md TASK-FE-COMMON-005
 *
 * @module hooks/useListQuery
 */

import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useCallback, useMemo } from 'react';
import { apiGet } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';

// ═══════════════════════════════════════════════════════════════════════════
// 类型定义
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 列表查询参数
 */
export interface ListParams {
  /** 当前页码 */
  page?: number;
  /** 每页条数 */
  page_size?: number;
  /** 其他查询参数 */
  [key: string]: string | number | boolean | undefined;
}

/**
 * useListQuery 配置选项
 */
export interface UseListQueryOptions<T> {
  /** 查询键（用于缓存） */
  queryKey: string[];
  /** API 端点路径 */
  endpoint: string;
  /** 默认查询参数 */
  defaultParams?: ListParams;
  /** TanStack Query 额外配置 */
  queryOptions?: Omit<
    UseQueryOptions<PaginatedResponse<T>, Error>,
    'queryKey' | 'queryFn'
  >;
}

/**
 * useListQuery 返回值
 */
export interface UseListQueryReturn<T> {
  /** 数据列表 */
  items: T[];
  /** 总记录数 */
  total: number;
  /** 当前页码 */
  page: number;
  /** 每页条数 */
  pageSize: number;
  /** 总页数 */
  totalPages: number;
  /** 是否加载中 */
  isLoading: boolean;
  /** 是否首次加载 */
  isFetching: boolean;
  /** 是否加载失败 */
  isError: boolean;
  /** 错误信息 */
  error: Error | null;
  /** 是否数据为空 */
  isEmpty: boolean;
  /** 当前查询参数 */
  params: ListParams;
  /** 更新查询参数（同步到 URL） */
  setParams: (newParams: ListParams) => void;
  /** 更新单个参数 */
  setParam: (key: string, value: string | number | boolean | undefined) => void;
  /** 切换页码 */
  setPage: (page: number) => void;
  /** 刷新数据 */
  refetch: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════
// Hook 实现
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 通用列表查询 Hook
 *
 * 功能:
 * - 自动从 URL 解析查询参数
 * - 参数变化时自动同步到 URL
 * - 支持分页、排序、筛选
 * - 集成 TanStack Query 缓存
 *
 * @example
 * ```tsx
 * const {
 *   items,
 *   total,
 *   page,
 *   isLoading,
 *   isEmpty,
 *   setPage,
 *   setParams,
 * } = useListQuery<User>({
 *   queryKey: ['users'],
 *   endpoint: '/api/v1/users',
 *   defaultParams: { page: 1, page_size: 20, status: 'active' },
 * });
 * ```
 */
export function useListQuery<T>({
  queryKey,
  endpoint,
  defaultParams = { page: 1, page_size: 20 },
  queryOptions,
}: UseListQueryOptions<T>): UseListQueryReturn<T> {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // 稳定化 defaultParams，避免对象引用变化导致重新计算
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const stableDefaultParams = useMemo(
    () => defaultParams,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(defaultParams)]
  );

  // 从 URL 解析参数，与默认值合并
  const params = useMemo<ListParams>(() => {
    const urlParams: ListParams = { ...stableDefaultParams };

    searchParams.forEach((value, key) => {
      if (key === 'page' || key === 'page_size') {
        const numValue = parseInt(value, 10);
        if (!isNaN(numValue)) {
          urlParams[key] = numValue;
        }
      } else if (value === 'true') {
        urlParams[key] = true;
      } else if (value === 'false') {
        urlParams[key] = false;
      } else {
        urlParams[key] = value;
      }
    });

    return urlParams;
  }, [searchParams, stableDefaultParams]);

  // 更新 URL 参数
  const setParams = useCallback(
    (newParams: ListParams) => {
      const urlParams = new URLSearchParams();

      Object.entries(newParams).forEach(([key, value]) => {
        // 排除空值和特殊值
        if (
          value !== undefined &&
          value !== '' &&
          value !== '__all__' &&
          value !== null
        ) {
          urlParams.set(key, String(value));
        }
      });

      const queryString = urlParams.toString();
      const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
      router.push(newUrl);
    },
    [router, pathname]
  );

  // 更新单个参数
  const setParam = useCallback(
    (key: string, value: string | number | boolean | undefined) => {
      setParams({ ...params, [key]: value });
    },
    [params, setParams]
  );

  // 切换页码
  const setPage = useCallback(
    (page: number) => {
      setParams({ ...params, page });
    },
    [params, setParams]
  );

  // 构建查询参数字符串
  const queryString = useMemo(() => {
    const urlParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (
        value !== undefined &&
        value !== '' &&
        value !== '__all__' &&
        value !== null
      ) {
        urlParams.set(key, String(value));
      }
    });

    return urlParams.toString();
  }, [params]);

  // 数据查询
  // 使用 queryString 作为缓存键的一部分，确保 queryKey 稳定性
  const query = useQuery<PaginatedResponse<T>, Error>({
    queryKey: [...queryKey, queryString],
    queryFn: async () => {
      const url = queryString ? `${endpoint}?${queryString}` : endpoint;
      return apiGet<PaginatedResponse<T>>(url);
    },
    staleTime: 2 * 60 * 1000, // 2 分钟
    ...queryOptions,
  });

  // 计算派生状态
  const items = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const page = query.data?.page ?? (params.page as number) ?? 1;
  const pageSize = query.data?.page_size ?? (params.page_size as number) ?? 20;
  const totalPages = query.data?.total_pages ?? Math.ceil(total / pageSize);
  const isEmpty = !query.isLoading && items.length === 0;

  return {
    items,
    total,
    page,
    pageSize,
    totalPages,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    error: query.error,
    isEmpty,
    params,
    setParams,
    setParam,
    setPage,
    refetch: query.refetch,
  };
}

export default useListQuery;
