/**
 * useTransfers Hook
 *
 * Mock data hook for Transfer module
 * Aligned with: TRANSFER_SOT.md v1.0
 */

import { useState, useCallback, useMemo } from 'react';
import type { TransferRequest, TransferFilters, TransferStatus } from '../types';

// Mock data for development
const mockTransfers: TransferRequest[] = [
  {
    id: 'tr-001',
    request_no: 'TRF-20250122-001',
    tenant_id: 'tenant-001',
    source_ad_account_id: 'acc-001',
    target_ad_account_id: 'acc-002',
    source_ad_account_name: '账户A-已死亡',
    target_ad_account_name: '账户B-活跃',
    supplier_id: 'sup-001',
    supplier_name: '腾讯广告',
    transfer_amount: 1234500, // cents
    status: 'completed',
    version: 2,
    created_by: 'user-001',
    created_by_name: '张三',
    notes: '账户异常关停，迁移余额',
    approved_by: 'user-002',
    approved_by_name: '李四',
    approved_at: '2025-01-22T10:30:00Z',
    completed_at: '2025-01-22T10:35:00Z',
    created_at: '2025-01-22T09:00:00Z',
    updated_at: '2025-01-22T10:35:00Z',
  },
  {
    id: 'tr-002',
    request_no: 'TRF-20250123-001',
    tenant_id: 'tenant-001',
    source_ad_account_id: 'acc-003',
    target_ad_account_id: 'acc-004',
    source_ad_account_name: '账户C-已死亡',
    target_ad_account_name: '账户D-活跃',
    supplier_id: 'sup-002',
    supplier_name: '巨量引擎',
    transfer_amount: 567800, // cents
    status: 'approved',
    version: 1,
    created_by: 'user-001',
    created_by_name: '张三',
    notes: '政策原因关停',
    approved_by: 'user-002',
    approved_by_name: '李四',
    approved_at: '2025-01-23T14:00:00Z',
    created_at: '2025-01-23T11:00:00Z',
    updated_at: '2025-01-23T14:00:00Z',
  },
  {
    id: 'tr-003',
    request_no: 'TRF-20250124-001',
    tenant_id: 'tenant-001',
    source_ad_account_id: 'acc-005',
    target_ad_account_id: 'acc-006',
    source_ad_account_name: '账户E-已死亡',
    target_ad_account_name: '账户F-活跃',
    supplier_id: 'sup-001',
    supplier_name: '腾讯广告',
    transfer_amount: 890000, // cents
    status: 'draft',
    version: 0,
    created_by: 'user-003',
    created_by_name: '王五',
    notes: '账户被封',
    created_at: '2025-01-24T09:00:00Z',
    updated_at: '2025-01-24T09:00:00Z',
  },
  {
    id: 'tr-004',
    request_no: 'TRF-20250124-002',
    tenant_id: 'tenant-001',
    source_ad_account_id: 'acc-007',
    target_ad_account_id: 'acc-008',
    source_ad_account_name: '账户G-已死亡',
    target_ad_account_name: '账户H-活跃',
    supplier_id: 'sup-002',
    supplier_name: '巨量引擎',
    transfer_amount: 345600, // cents
    status: 'rejected',
    version: 1,
    created_by: 'user-001',
    created_by_name: '张三',
    notes: '余额迁移申请',
    rejected_by: 'user-002',
    rejected_at: '2025-01-24T15:00:00Z',
    rejection_reason: '目标账户不符合条件',
    created_at: '2025-01-24T10:00:00Z',
    updated_at: '2025-01-24T15:00:00Z',
  },
];

interface UseTransfersResult {
  transfers: TransferRequest[];
  loading: boolean;
  error: Error | null;
  filters: TransferFilters;
  setFilters: (filters: TransferFilters) => void;
  stats: {
    total: number;
    byStatus: Record<TransferStatus, number>;
    totalAmount: number;
    pendingAmount: number;
  };
}

export function useTransfers(initialFilters: TransferFilters = {}): UseTransfersResult {
  const [filters, setFilters] = useState<TransferFilters>(initialFilters);
  const [loading] = useState(false);
  const [error] = useState<Error | null>(null);

  const filteredTransfers = useMemo(() => {
    return mockTransfers.filter((t) => {
      if (filters.status) {
        const statuses = Array.isArray(filters.status) ? filters.status : [filters.status];
        if (!statuses.includes(t.status)) return false;
      }
      if (filters.supplier_id && t.supplier_id !== filters.supplier_id) return false;
      return true;
    });
  }, [filters]);

  const stats = useMemo(() => {
    const byStatus: Record<TransferStatus, number> = {
      draft: 0,
      approved: 0,
      completed: 0,
      rejected: 0,
    };
    let totalAmount = 0;
    let pendingAmount = 0;

    mockTransfers.forEach((t) => {
      byStatus[t.status]++;
      totalAmount += t.transfer_amount;
      if (t.status === 'draft' || t.status === 'approved') {
        pendingAmount += t.transfer_amount;
      }
    });

    return {
      total: mockTransfers.length,
      byStatus,
      totalAmount,
      pendingAmount,
    };
  }, []);

  const handleSetFilters = useCallback((newFilters: TransferFilters) => {
    setFilters(newFilters);
  }, []);

  return {
    transfers: filteredTransfers,
    loading,
    error,
    filters,
    setFilters: handleSetFilters,
    stats,
  };
}
