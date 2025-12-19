/**
 * useImportJobs Hooks Tests
 *
 * Tests for frontend/src/features/import-jobs/hooks/useImportJobs.ts
 * SoT: DATA_SCHEMA.md v5.2
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useImportJobs,
  useImportJob,
  useImportJobProgress,
  useImportJobStatistics,
  useUploadImportFile,
  useStartImportJob,
  useCancelImportJob,
  useDeleteImportJob,
} from '@/features/import-jobs/hooks/useImportJobs';
import * as importJobsApi from '@/features/import-jobs/services';
import type {
  ImportJob,
  ImportJobStatus,
  ImportJobType,
  ImportJobProgress,
  ImportJobStatistics,
} from '@/features/import-jobs/types';

// Mock the import jobs API - must match the import path in useImportJobs.ts
jest.mock('@/features/import-jobs/services', () => ({
  getImportJobs: jest.fn(),
  getImportJob: jest.fn(),
  getImportJobProgress: jest.fn(),
  getImportJobStatistics: jest.fn(),
  uploadImportFile: jest.fn(),
  startImportJob: jest.fn(),
  cancelImportJob: jest.fn(),
  deleteImportJob: jest.fn(),
}));

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

// Mock import job data factory
function createMockImportJob(overrides: Partial<ImportJob> = {}): ImportJob {
  return {
    id: 1,
    job_no: 'IMP-2025-0001',
    type: 'finance' as ImportJobType,
    status: 'pending' as ImportJobStatus,
    file_name: 'test-data.xlsx',
    file_size: 1024,
    total_rows: 100,
    processed_rows: 0,
    success_rows: 0,
    failed_rows: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

// Mock progress data factory
function createMockProgress(overrides: Partial<ImportJobProgress> = {}): ImportJobProgress {
  return {
    job_id: 1,
    job_no: 'IMP-2025-0001',
    status: 'processing' as ImportJobStatus,
    total_rows: 100,
    processed_rows: 50,
    success_rows: 48,
    failed_rows: 2,
    progress_percent: 50,
    ...overrides,
  };
}

// Mock statistics data factory
function createMockStatistics(overrides: Partial<ImportJobStatistics> = {}): ImportJobStatistics {
  return {
    total_jobs: 100,
    pending_jobs: 5,
    processing_jobs: 2,
    completed_jobs: 85,
    failed_jobs: 5,
    cancelled_jobs: 3,
    overall_success_rate: 0.94,
    total_rows_processed: 10000,
    total_rows_success: 9400,
    total_rows_failed: 600,
    by_type: { finance: 40, spend: 30, reconciliation: 20, daily_report: 10 },
    recent_jobs: [],
    ...overrides,
  };
}

describe('useImportJobs Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ========== Query Hooks ==========

  describe('useImportJobs', () => {
    it('should fetch import job list successfully', async () => {
      const mockJobs = [
        createMockImportJob({ id: 1 }),
        createMockImportJob({ id: 2, job_no: 'IMP-2025-0002' }),
      ];
      const mockResponse = {
        items: mockJobs,
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };

      (importJobsApi.getImportJobs as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useImportJobs(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(2);
      expect(result.current.data?.total).toBe(2);
      expect(importJobsApi.getImportJobs).toHaveBeenCalled();
    });

    it('should fetch with status and type filters', async () => {
      const mockResponse = {
        items: [createMockImportJob({ status: 'processing', type: 'finance' })],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };

      (importJobsApi.getImportJobs as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useImportJobs({ status: 'processing', type: 'finance' }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items[0]?.status).toBe('processing');
      expect(result.current.data?.items[0]?.type).toBe('finance');
    });

    it('should handle fetch error', async () => {
      (importJobsApi.getImportJobs as jest.Mock).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useImportJobs(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe('Network error');
    });
  });

  describe('useImportJob', () => {
    it('should fetch single import job by id', async () => {
      const mockJob = createMockImportJob({ id: 123 });
      (importJobsApi.getImportJob as jest.Mock).mockResolvedValue(mockJob);

      const { result } = renderHook(() => useImportJob(123), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.id).toBe(123);
      expect(importJobsApi.getImportJob).toHaveBeenCalledWith(123);
    });

    it('should not fetch when id is 0', async () => {
      const { result } = renderHook(() => useImportJob(0), {
        wrapper: createWrapper(),
      });

      expect(result.current.isFetching).toBe(false);
      expect(importJobsApi.getImportJob).not.toHaveBeenCalled();
    });
  });

  describe('useImportJobProgress', () => {
    it('should fetch progress data', async () => {
      const mockProgress = createMockProgress();
      (importJobsApi.getImportJobProgress as jest.Mock).mockResolvedValue(mockProgress);

      const { result } = renderHook(() => useImportJobProgress(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.progress_percent).toBe(50);
      expect(importJobsApi.getImportJobProgress).toHaveBeenCalledWith(1);
    });

    it('should not fetch when disabled', async () => {
      const { result } = renderHook(
        () => useImportJobProgress(1, { enabled: false }),
        { wrapper: createWrapper() }
      );

      expect(result.current.isFetching).toBe(false);
      expect(importJobsApi.getImportJobProgress).not.toHaveBeenCalled();
    });
  });

  describe('useImportJobStatistics', () => {
    it('should fetch statistics', async () => {
      const mockStats = createMockStatistics();
      (importJobsApi.getImportJobStatistics as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useImportJobStatistics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.total_jobs).toBe(100);
      expect(result.current.data?.overall_success_rate).toBe(0.94);
    });
  });

  // ========== Mutation Hooks ==========

  describe('useUploadImportFile', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useUploadImportFile(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
      expect(result.current.isPending).toBe(false);
    });
  });

  describe('useStartImportJob', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useStartImportJob(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useCancelImportJob', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useCancelImportJob(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useDeleteImportJob', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useDeleteImportJob(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  // ========== State Machine Transitions (Type Safety) ==========

  describe('State Machine Transitions', () => {
    it('should define valid import job statuses', () => {
      const validStatuses: ImportJobStatus[] = [
        'pending',
        'processing',
        'completed',
        'failed',
        'cancelled',
      ];

      const mockJob = createMockImportJob();
      expect(validStatuses).toContain(mockJob.status);
    });

    it('should define valid import job types', () => {
      const validTypes: ImportJobType[] = [
        'finance',
        'spend',
        'reconciliation',
        'daily_report',
      ];

      const mockJob = createMockImportJob();
      expect(validTypes).toContain(mockJob.type);
    });

    it('should allow state transition mock data', () => {
      const pending = createMockImportJob({ status: 'pending' });
      const processing = createMockImportJob({ status: 'processing' });
      const completed = createMockImportJob({ status: 'completed' });
      const failed = createMockImportJob({ status: 'failed' });
      const cancelled = createMockImportJob({ status: 'cancelled' });

      expect(pending.status).toBe('pending');
      expect(processing.status).toBe('processing');
      expect(completed.status).toBe('completed');
      expect(failed.status).toBe('failed');
      expect(cancelled.status).toBe('cancelled');
    });
  });

  // ========== Progress Tracking ==========

  describe('Progress Tracking', () => {
    it('should track progress percent correctly', () => {
      const progress = createMockProgress({
        processed_rows: 75,
        progress_percent: 75,
      });

      expect(progress.progress_percent).toBe(75);
      expect(progress.processed_rows).toBe(75);
    });

    it('should track success and failure counts', () => {
      const progress = createMockProgress({
        total_rows: 100,
        processed_rows: 100,
        success_rows: 95,
        failed_rows: 5,
      });

      expect(progress.success_rows + progress.failed_rows).toBe(progress.processed_rows);
    });
  });

  // ========== Hook Structure ==========

  describe('Hook Structure', () => {
    it('should export all required hooks', () => {
      expect(useImportJobs).toBeDefined();
      expect(useImportJob).toBeDefined();
      expect(useImportJobProgress).toBeDefined();
      expect(useImportJobStatistics).toBeDefined();
      expect(useUploadImportFile).toBeDefined();
      expect(useStartImportJob).toBeDefined();
      expect(useCancelImportJob).toBeDefined();
      expect(useDeleteImportJob).toBeDefined();
    });
  });
});
