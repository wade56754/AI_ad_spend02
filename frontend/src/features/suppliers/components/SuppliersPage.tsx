/**
 * SuppliersPage Component
 *
 * Main page component for supplier management
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

'use client';

import React from 'react';
import { Building2, Plus, Search, Filter, RefreshCw } from 'lucide-react';
import { LoadingSpinner } from '@/modules/shared/components/feedback/LoadingSpinner';
import { ErrorDisplay } from '@/modules/shared/components/feedback/ErrorDisplay';
import {
  useSuppliers,
  useSupplierStatistics,
  useCreateSupplier,
  useUpdateSupplier,
  useDeleteSupplier,
  useActivateSupplier,
  useSuspendSupplier,
} from '../hooks';
import type {
  Supplier,
  SupplierListParams,
  SupplierCreateInput,
  SupplierUpdateInput,
  SupplierStatus,
} from '../types';
import { SUPPLIER_STATUS_CONFIG, SupplierStatus as SupplierStatusEnum } from '../types';
import { SuppliersTable } from './SuppliersTable';
import { SupplierForm } from './SupplierForm';

export function SuppliersPage() {
  // State
  const [params, setParams] = React.useState<SupplierListParams>({
    page: 1,
    page_size: 10,
  });
  const [showForm, setShowForm] = React.useState(false);
  const [editingSupplier, setEditingSupplier] = React.useState<Supplier | null>(null);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterStatus, setFilterStatus] = React.useState<SupplierStatus | ''>('');
  const [deleteConfirm, setDeleteConfirm] = React.useState<Supplier | null>(null);

  // Queries
  const {
    data: suppliersData,
    isLoading,
    isError,
    error,
    refetch,
  } = useSuppliers(params);

  const { data: statistics } = useSupplierStatistics();

  // Mutations
  const createMutation = useCreateSupplier({
    onSuccess: () => {
      setShowForm(false);
      refetch();
    },
  });

  const updateMutation = useUpdateSupplier({
    onSuccess: () => {
      setShowForm(false);
      setEditingSupplier(null);
      refetch();
    },
  });

  const deleteMutation = useDeleteSupplier({
    onSuccess: () => {
      setDeleteConfirm(null);
      refetch();
    },
  });

  const activateMutation = useActivateSupplier({
    onSuccess: () => refetch(),
  });

  const suspendMutation = useSuspendSupplier({
    onSuccess: () => refetch(),
  });

  // Handlers
  const handleSearch = () => {
    setParams((prev) => ({
      ...prev,
      search: searchQuery || undefined,
      status: filterStatus || undefined,
      page: 1,
    }));
  };

  const handleReset = () => {
    setSearchQuery('');
    setFilterStatus('');
    setParams({ page: 1, page_size: 10 });
  };

  const handleView = (_supplier: Supplier) => {
    // TODO: 实现供应商详情抽屉
  };

  const handleEdit = (supplier: Supplier) => {
    setEditingSupplier(supplier);
    setShowForm(true);
  };

  const handleDelete = (supplier: Supplier) => {
    setDeleteConfirm(supplier);
  };

  const handleConfirmDelete = () => {
    if (deleteConfirm) {
      deleteMutation.mutate(deleteConfirm.id);
    }
  };

  const handleStatusChange = (supplier: Supplier, newStatus: SupplierStatus) => {
    if (newStatus === 'active') {
      activateMutation.mutate(supplier.id);
    } else if (newStatus === 'suspended') {
      suspendMutation.mutate(supplier.id);
    }
  };

  const handleFormSubmit = (data: SupplierCreateInput | SupplierUpdateInput) => {
    if (editingSupplier) {
      updateMutation.mutate({ id: editingSupplier.id, input: data as SupplierUpdateInput });
    } else {
      createMutation.mutate(data as SupplierCreateInput);
    }
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingSupplier(null);
  };

  const handlePageChange = (page: number) => {
    setParams((prev) => ({ ...prev, page }));
  };

  const suppliers = suppliersData?.items || [];
  const totalCount = suppliersData?.total || 0;
  const totalPages = Math.ceil(totalCount / (params.page_size || 10));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Building2 className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">供应商管理</h1>
                <p className="text-sm text-gray-500">管理户商信息、账户关联和财务数据</p>
              </div>
            </div>
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              新增供应商
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Cards - v3.0 优化版 */}
      {statistics && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">供应商总数</p>
                  <p className="text-3xl font-bold text-gray-900 tabular-nums">{statistics.total_suppliers}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Building2 className="h-5 w-5 text-slate-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">活跃供应商</p>
                  <p className="text-3xl font-bold text-green-600 tabular-nums">{statistics.active_suppliers}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                  <Building2 className="h-5 w-5 text-green-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">管理账户数</p>
                  <p className="text-3xl font-bold text-blue-600 tabular-nums">{statistics.total_accounts_managed}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                  <Building2 className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">总消耗</p>
                  <p className="text-3xl font-bold text-gray-900 tabular-nums">
                    ${statistics.total_spend?.toLocaleString() || 0}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
                  <Building2 className="h-5 w-5 text-amber-600" />
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
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="搜索供应商名称..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as SupplierStatus | '')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">全部状态</option>
                {Object.entries(SUPPLIER_STATUS_CONFIG).map(([value, config]) => (
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
              <SuppliersTable
                suppliers={suppliers}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onStatusChange={handleStatusChange}
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

      {/* Form Modal */}
      {showForm && (
        <SupplierForm
          supplier={editingSupplier}
          onSubmit={handleFormSubmit}
          onCancel={handleFormClose}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {/* Delete Confirmation */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50" onClick={() => setDeleteConfirm(null)} />
            <div className="relative w-full max-w-md bg-white rounded-lg shadow-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">确认删除</h3>
              <p className="text-gray-500 mb-4">
                确定要删除供应商 <span className="font-medium">{deleteConfirm.name}</span> 吗？此操作不可撤销。
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmDelete}
                  disabled={deleteMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {deleteMutation.isPending ? '删除中...' : '确认删除'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SuppliersPage;
