/**
 * useProjects Hook
 *
 * 项目列表数据获取和状态管理
 */

'use client';

import { useState, useCallback } from 'react';
import type { Project, ProjectFilters, ProjectSummary } from '../types';

// Mock 数据 - 后续接入真实 API
const MOCK_PROJECTS: Project[] = [
  {
    id: 'proj-001',
    name: '春季促销活动',
    description: '2024 春季线上促销广告投放',
    client_name: '某电商平台',
    status: 'active',
    budget_total: 500000,
    budget_daily: 20000,
    spent_total: 235000,
    spent_today: 18500,
    ad_account_count: 3,
    start_date: '2024-03-01',
    end_date: '2024-04-30',
    created_at: '2024-02-15T10:00:00Z',
    updated_at: '2024-03-20T15:30:00Z',
  },
  {
    id: 'proj-002',
    name: '品牌曝光计划',
    description: '全年品牌曝光广告投放',
    client_name: '某消费品牌',
    status: 'active',
    budget_total: 1200000,
    budget_daily: 35000,
    spent_total: 780000,
    spent_today: 32000,
    ad_account_count: 5,
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    created_at: '2023-12-01T10:00:00Z',
    updated_at: '2024-03-20T16:00:00Z',
  },
  {
    id: 'proj-003',
    name: '新品上市推广',
    description: '新产品线上市推广',
    client_name: '某科技公司',
    status: 'paused',
    budget_total: 300000,
    budget_daily: 15000,
    spent_total: 120000,
    spent_today: 0,
    ad_account_count: 2,
    start_date: '2024-02-01',
    end_date: '2024-05-31',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-03-15T10:00:00Z',
  },
];

const MOCK_SUMMARY: ProjectSummary = {
  total_projects: 3,
  active_projects: 2,
  total_budget: 2000000,
  total_spent: 1135000,
  today_spent: 50500,
};

interface UseProjectsResult {
  projects: Project[];
  summary: ProjectSummary;
  loading: boolean;
  error: Error | null;
  filters: ProjectFilters;
  setFilters: (filters: ProjectFilters) => void;
  refresh: () => Promise<void>;
}

export function useProjects(initialFilters: ProjectFilters = {}): UseProjectsResult {
  const [projects, setProjects] = useState<Project[]>([]);
  const [summary, setSummary] = useState<ProjectSummary>(MOCK_SUMMARY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [filters, setFilters] = useState<ProjectFilters>(initialFilters);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 500));

      let filtered = [...MOCK_PROJECTS];

      // 应用筛选
      if (filters.status) {
        const statuses = Array.isArray(filters.status) ? filters.status : [filters.status];
        filtered = filtered.filter(p => statuses.includes(p.status));
      }

      if (filters.search) {
        const search = filters.search.toLowerCase();
        filtered = filtered.filter(
          p => p.name.toLowerCase().includes(search) ||
               p.client_name.toLowerCase().includes(search)
        );
      }

      setProjects(filtered);
      setSummary(MOCK_SUMMARY);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('加载失败'));
    } finally {
      setLoading(false);
    }
  }, [filters]);

  return {
    projects,
    summary,
    loading,
    error,
    filters,
    setFilters,
    refresh,
  };
}

export default useProjects;
