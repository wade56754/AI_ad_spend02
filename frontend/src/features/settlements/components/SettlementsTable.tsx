/**
 * SettlementsTable Component
 *
 * Table component for displaying settlement list
 * SoT 对齐: DATA_SCHEMA.md v5.2, LEDGER_SOT.md v1.1
 */

'use client';

import React from 'react';
import {
  FileText,
  MoreVertical,
  Eye,
  Edit,
  Send,
  CheckCircle,
  XCircle,
  CreditCard,
  Ban,
  AlertTriangle,
} from 'lucide-react';
import { StatusBadge } from '@/modules/shared/components/ui/StatusBadge';
import type { Settlement, SettlementStatus } from '../types';
import {
  SETTLEMENT_STATUS_CONFIG,
  PAYMENT_STATUS_CONFIG,
  SETTLEMENT_TYPE_CONFIG,
} from '../types';

interface SettlementsTableProps {
  settlements: Settlement[];
  onView?: (settlement: Settlement) => void;
  onEdit?: (settlement: Settlement) => void;
  onSubmit?: (settlement: Settlement) => void;
  onApprove?: (settlement: Settlement, action: 'approve' | 'reject') => void;
  onRecordPayment?: (settlement: Settlement) => void;
  onCancel?: (settlement: Settlement) => void;
  loading?: boolean;
}

export function SettlementsTable({
  settlements,
  onView,
  onEdit,
  onSubmit,
  onApprove,
  onRecordPayment,
  onCancel,
  loading = false,
}: SettlementsTableProps) {
  const [openMenuId, setOpenMenuId] = React.useState<number | null>(null);

  const toggleMenu = (id: number) => {
    setOpenMenuId(openMenuId === id ? null : id);
  };

  const handleAction = (action: () => void) => {
    action();
    setOpenMenuId(null);
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: currency || 'CNY',
    }).format(amount);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  const isOverdue = (settlement: Settlement) => {
    if (!settlement.due_date) return false;
    if (settlement.status === 'COMPLETED' || settlement.status === 'CANCELLED') return false;
    return new Date(settlement.due_date) < new Date();
  };

  // 根据状态判断可用操作
  const canEdit = (status: SettlementStatus) => ['DRAFT', 'REJECTED'].includes(status);
  const canSubmit = (status: SettlementStatus) => status === 'DRAFT';
  const canApprove = (status: SettlementStatus) => status === 'PENDING';
  const canRecordPayment = (status: SettlementStatus) => ['APPROVED', 'PROCESSING'].includes(status);
  const canCancel = (status: SettlementStatus) => ['DRAFT', 'APPROVED'].includes(status);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-12 bg-gray-200 rounded mb-2"></div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 bg-gray-100 rounded mb-2"></div>
        ))}
      </div>
    );
  }

  if (settlements.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-semibold text-gray-900">暂无结算记录</h3>
        <p className="mt-1 text-sm text-gray-500">点击新增按钮创建第一笔结算</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              结算单号
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              类型
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              对象
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              金额
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              结算期间
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              状态
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              支付状态
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {settlements.map((settlement) => {
            const statusConfig = SETTLEMENT_STATUS_CONFIG[settlement.status];
            const paymentStatusConfig = PAYMENT_STATUS_CONFIG[settlement.payment_status];
            const typeConfig = SETTLEMENT_TYPE_CONFIG[settlement.type];
            const overdue = isOverdue(settlement);

            return (
              <tr key={settlement.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 bg-gray-100 rounded-full flex items-center justify-center">
                      <FileText className="h-5 w-5 text-gray-500" />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {settlement.settlement_no}
                      </div>
                      <div className="text-sm text-gray-500">
                        {formatDate(settlement.created_at)}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-900">{typeConfig.label}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {settlement.type === 'SUPPLIER'
                      ? settlement.supplier_name || '-'
                      : settlement.client_name || '-'}
                  </div>
                  {settlement.project_name && (
                    <div className="text-sm text-gray-500">
                      {settlement.project_name}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {formatCurrency(settlement.amount, settlement.currency)}
                  </div>
                  {settlement.paid_amount > 0 && settlement.paid_amount < settlement.amount && (
                    <div className="text-sm text-gray-500">
                      已付 {formatCurrency(settlement.paid_amount, settlement.currency)}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {formatDate(settlement.settlement_period_start)} ~
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(settlement.settlement_period_end)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge
                    label={statusConfig.label}
                    variant={statusConfig.color}
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <StatusBadge
                      label={paymentStatusConfig.label}
                      variant={paymentStatusConfig.color}
                      size="sm"
                    />
                    {overdue && (
                      <span className="inline-flex items-center text-red-600" title="已逾期">
                        <AlertTriangle className="h-4 w-4" />
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="relative inline-block text-left">
                    <button
                      onClick={() => toggleMenu(settlement.id)}
                      className="p-2 rounded-full hover:bg-gray-100"
                    >
                      <MoreVertical className="h-4 w-4 text-gray-500" />
                    </button>

                    {openMenuId === settlement.id && (
                      <>
                        <div
                          className="fixed inset-0 z-10"
                          onClick={() => setOpenMenuId(null)}
                        />
                        <div className="absolute right-0 z-20 mt-2 w-48 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
                          <div className="py-1">
                            {onView && (
                              <button
                                onClick={() => handleAction(() => onView(settlement))}
                                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                              >
                                <Eye className="mr-3 h-4 w-4" />
                                查看详情
                              </button>
                            )}
                            {onEdit && canEdit(settlement.status) && (
                              <button
                                onClick={() => handleAction(() => onEdit(settlement))}
                                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                              >
                                <Edit className="mr-3 h-4 w-4" />
                                编辑
                              </button>
                            )}
                            {onSubmit && canSubmit(settlement.status) && (
                              <button
                                onClick={() => handleAction(() => onSubmit(settlement))}
                                className="flex items-center w-full px-4 py-2 text-sm text-blue-700 hover:bg-gray-100"
                              >
                                <Send className="mr-3 h-4 w-4" />
                                提交审批
                              </button>
                            )}
                            {onApprove && canApprove(settlement.status) && (
                              <>
                                <button
                                  onClick={() => handleAction(() => onApprove(settlement, 'approve'))}
                                  className="flex items-center w-full px-4 py-2 text-sm text-green-700 hover:bg-gray-100"
                                >
                                  <CheckCircle className="mr-3 h-4 w-4" />
                                  审批通过
                                </button>
                                <button
                                  onClick={() => handleAction(() => onApprove(settlement, 'reject'))}
                                  className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-gray-100"
                                >
                                  <XCircle className="mr-3 h-4 w-4" />
                                  拒绝
                                </button>
                              </>
                            )}
                            {onRecordPayment && canRecordPayment(settlement.status) && (
                              <button
                                onClick={() => handleAction(() => onRecordPayment(settlement))}
                                className="flex items-center w-full px-4 py-2 text-sm text-blue-700 hover:bg-gray-100"
                              >
                                <CreditCard className="mr-3 h-4 w-4" />
                                记录支付
                              </button>
                            )}
                            {onCancel && canCancel(settlement.status) && (
                              <button
                                onClick={() => handleAction(() => onCancel(settlement))}
                                className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-gray-100"
                              >
                                <Ban className="mr-3 h-4 w-4" />
                                取消结算
                              </button>
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default SettlementsTable;
