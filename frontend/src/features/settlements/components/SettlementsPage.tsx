/**
 * SettlementsPage Component - 通用结算管理
 *
 * SoT: docs/10.module-specs/D1-monthly-settlement.md (月度结算规格)
 * SoT: DATA_SCHEMA.md v5.2 (settlement entity)
 * SoT: LEDGER_SOT.md v1.1 (ledger integration)
 * SoT: STATE_MACHINE.md v2.6 Section 12 (结算状态机)
 *
 * 一句话定义: 管理供应商和客户的结算审批流程
 *
 * 本页面为通用结算 (Supplier/Client Settlement):
 * - 状态机 (7 状态): DRAFT → PENDING → APPROVED → PROCESSING → COMPLETED
 *                            ↘ REJECTED
 *                    任意 → CANCELLED
 *
 * 月度项目结算请使用 MonthlySettlementsPage 组件:
 * - 状态机 (4 状态): pending → draft → confirmed → locked
 * - SoT: D1-monthly-settlement.md §2.4
 *
 * 页面布局:
 * ┌─────────────────────────────────────────────────┐
 * │ Header: 标题 + 新增结算按钮                       │
 * ├─────────────────────────────────────────────────┤
 * │ KPI Cards: 总数 | 总金额 | 待结算 | 已支付 | 逾期   │
 * ├─────────────────────────────────────────────────┤
 * │ Filters: 类型筛选 | 状态筛选 | 搜索/重置/刷新      │
 * ├─────────────────────────────────────────────────┤
 * │ Table: 结算明细列表 + 操作按钮                    │
 * ├─────────────────────────────────────────────────┤
 * │ Pagination: 分页控制                             │
 * └─────────────────────────────────────────────────┘
 *
 * 权限 (MASTER.md v4.4 §2.4):
 * - ceo, finance: 查看全部、审批、记录支付
 * - admin: 全部权限
 *
 * Author: AI 代码工厂 v2.4
 */

'use client';

import React from 'react';
import { FileText, Plus, Filter, RefreshCw, AlertTriangle } from 'lucide-react';
import { LoadingSpinner } from '@/modules/shared/components/feedback/LoadingSpinner';
import { ErrorDisplay } from '@/modules/shared/components/feedback/ErrorDisplay';
import {
  useSettlements,
  useSettlementStatistics,
  useSubmitSettlement,
  useApproveSettlement,
  useCancelSettlement,
} from '../hooks';
import type {
  Settlement,
  SettlementListParams,
  SettlementStatus,
  SettlementType,
} from '../types';
import { SETTLEMENT_STATUS_CONFIG, SETTLEMENT_TYPE_CONFIG } from '../types';
import { SettlementsTable } from './SettlementsTable';

export function SettlementsPage() {
  // State
  const [params, setParams] = React.useState<SettlementListParams>({
    page: 1,
    page_size: 10,
  });
  const [filterStatus, setFilterStatus] = React.useState<SettlementStatus | ''>('');
  const [filterType, setFilterType] = React.useState<SettlementType | ''>('');
  const [cancelConfirm, setCancelConfirm] = React.useState<Settlement | null>(null);
  const [cancelReason, setCancelReason] = React.useState('');
  const [approveConfirm, setApproveConfirm] = React.useState<{
    settlement: Settlement;
    action: 'approve' | 'reject';
  } | null>(null);
  const [rejectReason, setRejectReason] = React.useState('');

  // Queries
  const {
    data: settlementsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useSettlements(params);

  const { data: statistics } = useSettlementStatistics({});

  // Mutations
  const submitMutation = useSubmitSettlement({
    onSuccess: () => {
      refetch();
    },
  });

  const approveMutation = useApproveSettlement({
    onSuccess: () => {
      setApproveConfirm(null);
      setRejectReason('');
      refetch();
    },
  });

  const cancelMutation = useCancelSettlement({
    onSuccess: () => {
      setCancelConfirm(null);
      setCancelReason('');
      refetch();
    },
  });

  // Handlers
  const handleSearch = () => {
    setParams((prev) => ({
      ...prev,
      status: filterStatus || undefined,
      settlement_type: filterType || undefined,
      page: 1,
    }));
  };

  const handleReset = () => {
    setFilterStatus('');
    setFilterType('');
    setParams({ page: 1, page_size: 10 });
  };

  const handleView = (_settlement: Settlement) => {
    // TODO: 实现结算单详情查看
  };

  const handleEdit = (_settlement: Settlement) => {
    // TODO: 实现结算单编辑
  };

  const handleSubmit = (settlement: Settlement) => {
    submitMutation.mutate(settlement.id);
  };

  const handleApprove = (settlement: Settlement, action: 'approve' | 'reject') => {
    setApproveConfirm({ settlement, action });
  };

  const handleConfirmApprove = () => {
    if (approveConfirm) {
      approveMutation.mutate({
        id: approveConfirm.settlement.id,
        input: {
          action: approveConfirm.action,
          reason: approveConfirm.action === 'reject' ? rejectReason : undefined,
        },
      });
    }
  };

  const handleRecordPayment = (_settlement: Settlement) => {
    // TODO: 实现付款登记
  };

  const handleCancel = (settlement: Settlement) => {
    setCancelConfirm(settlement);
  };

  const handleConfirmCancel = () => {
    if (cancelConfirm) {
      cancelMutation.mutate({
        id: cancelConfirm.id,
        reason: cancelReason || undefined,
      });
    }
  };

  const handlePageChange = (page: number) => {
    setParams((prev) => ({ ...prev, page }));
  };

  const settlements = settlementsData?.items || [];
  const totalCount = settlementsData?.meta?.pagination?.total || 0;
  const totalPages = Math.ceil(totalCount / (params.page_size || 10));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">结算管理</h1>
                <p className="text-sm text-gray-500">管理供应商和客户结算</p>
              </div>
            </div>
            <button
              onClick={() => { /* TODO: 实现新增结算表单 */ }}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              新增结算
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Cards - v3.0 优化版 */}
      {statistics && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">结算总数</p>
                  <p className="text-3xl font-bold text-gray-900 tabular-nums">{statistics.total_settlements}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-slate-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">总金额</p>
                  <p className="text-3xl font-bold text-gray-900 tabular-nums">
                    ¥{statistics.total_amount?.toLocaleString() || 0}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">待结算金额</p>
                  <p className="text-3xl font-bold text-amber-600 tabular-nums">
                    ¥{statistics.pending_amount?.toLocaleString() || 0}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-amber-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">已支付金额</p>
                  <p className="text-3xl font-bold text-green-600 tabular-nums">
                    ¥{statistics.paid_amount?.toLocaleString() || 0}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-green-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">逾期</p>
                    {(statistics.overdue_count || 0) > 0 && (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    )}
                  </div>
                  <p className="text-3xl font-bold text-red-600 tabular-nums">
                    {statistics.overdue_count || 0}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters - v3.0 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as SettlementType | '')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">全部类型</option>
                {Object.entries(SETTLEMENT_TYPE_CONFIG).map(([value, config]) => (
                  <option key={value} value={value}>
                    {config.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as SettlementStatus | '')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">全部状态</option>
                {Object.entries(SETTLEMENT_STATUS_CONFIG).map(([value, config]) => (
                  <option key={value} value={value}>
                    {config.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              搜索
            </button>

            <button
              onClick={handleReset}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              重置
            </button>

            <button
              onClick={() => refetch()}
              className="p-2 border border-gray-300 rounded-md hover:bg-gray-50"
              title="刷新"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content - v3.0 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" label="加载中..." />
            </div>
          ) : isError ? (
            <div className="p-4">
              <ErrorDisplay
                error={error}
                onRetry={() => refetch()}
              />
            </div>
          ) : (
            <>
              <SettlementsTable
                settlements={settlements}
                onView={handleView}
                onEdit={handleEdit}
                onSubmit={handleSubmit}
                onApprove={handleApprove}
                onRecordPayment={handleRecordPayment}
                onCancel={handleCancel}
              />

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-6 py-4 border-t">
                  <div className="text-sm text-gray-500">
                    共 {totalCount} 条记录，第 {params.page} / {totalPages} 页
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handlePageChange(params.page! - 1)}
                      disabled={params.page === 1}
                      className="px-3 py-1 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      上一页
                    </button>
                    <button
                      onClick={() => handlePageChange(params.page! + 1)}
                      disabled={params.page === totalPages}
                      className="px-3 py-1 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      下一页
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Cancel Confirmation Modal */}
      {cancelConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50" onClick={() => setCancelConfirm(null)} />
            <div className="relative w-full max-w-md bg-white rounded-lg shadow-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">确认取消</h3>
              <p className="text-gray-500 mb-4">
                确定要取消结算单 <span className="font-medium">{cancelConfirm.settlement_no}</span> 吗？
              </p>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  取消原因（可选）
                </label>
                <textarea
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="请输入取消原因..."
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setCancelConfirm(null);
                    setCancelReason('');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmCancel}
                  disabled={cancelMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {cancelMutation.isPending ? '处理中...' : '确认取消'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Approve/Reject Confirmation Modal */}
      {approveConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50" onClick={() => setApproveConfirm(null)} />
            <div className="relative w-full max-w-md bg-white rounded-lg shadow-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {approveConfirm.action === 'approve' ? '确认审批通过' : '确认拒绝'}
              </h3>
              <p className="text-gray-500 mb-4">
                {approveConfirm.action === 'approve'
                  ? '确定要审批通过结算单 ' + approveConfirm.settlement.settlement_no + ' 吗？'
                  : '确定要拒绝结算单 ' + approveConfirm.settlement.settlement_no + ' 吗？'}
              </p>
              {approveConfirm.action === 'reject' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    拒绝原因
                  </label>
                  <textarea
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="请输入拒绝原因..."
                    required
                  />
                </div>
              )}
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setApproveConfirm(null);
                    setRejectReason('');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmApprove}
                  disabled={approveMutation.isPending || (approveConfirm.action === 'reject' && !rejectReason)}
                  className={'px-4 py-2 text-sm font-medium text-white rounded-md disabled:opacity-50 ' +
                    (approveConfirm.action === 'approve'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700')}
                >
                  {approveMutation.isPending
                    ? '处理中...'
                    : approveConfirm.action === 'approve'
                    ? '确认通过'
                    : '确认拒绝'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SettlementsPage;
