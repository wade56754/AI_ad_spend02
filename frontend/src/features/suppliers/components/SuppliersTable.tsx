/**
 * SuppliersTable Component
 *
 * Table component for displaying supplier list
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

'use client';

import React from 'react';
import { Building2, Mail, Phone, MoreVertical, Eye, Edit, Trash2, Ban, CheckCircle } from 'lucide-react';
import { StatusBadge } from '@/modules/shared/components/ui/StatusBadge';
import type { Supplier, SupplierStatus } from '../types';
import { SUPPLIER_STATUS_CONFIG, PAYMENT_METHOD_CONFIG } from '../types';

interface SuppliersTableProps {
  suppliers: Supplier[];
  onView?: (supplier: Supplier) => void;
  onEdit?: (supplier: Supplier) => void;
  onDelete?: (supplier: Supplier) => void;
  onStatusChange?: (supplier: Supplier, newStatus: SupplierStatus) => void;
  loading?: boolean;
}

export function SuppliersTable({
  suppliers,
  onView,
  onEdit,
  onDelete,
  onStatusChange,
  loading = false,
}: SuppliersTableProps) {
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
      currency: currency || 'USD',
    }).format(amount);
  };

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

  if (suppliers.length === 0) {
    return (
      <div className="text-center py-12">
        <Building2 className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-semibold text-gray-900">暂无供应商</h3>
        <p className="mt-1 text-sm text-gray-500">点击新增按钮添加第一个供应商</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              供应商
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              联系方式
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              支付方式
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              账户数
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              总消耗
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              状态
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {suppliers.map((supplier) => {
            const statusConfig = SUPPLIER_STATUS_CONFIG[supplier.status];
            const paymentConfig = PAYMENT_METHOD_CONFIG[supplier.payment_method];

            return (
              <tr key={supplier.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 bg-gray-100 rounded-full flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-gray-500" />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {supplier.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {supplier.country || '-'} · {supplier.base_currency}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {supplier.contact_name || '-'}
                  </div>
                  <div className="text-sm text-gray-500 flex items-center gap-2">
                    {supplier.contact_email && (
                      <span className="flex items-center gap-1">
                        <Mail className="h-3 w-3" />
                        {supplier.contact_email}
                      </span>
                    )}
                    {supplier.contact_phone && (
                      <span className="flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        {supplier.contact_phone}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-900">{paymentConfig.label}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {supplier.total_accounts}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatCurrency(supplier.total_spend, supplier.base_currency)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge
                    label={statusConfig.label}
                    variant={statusConfig.color}
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="relative inline-block text-left">
                    <button
                      onClick={() => toggleMenu(supplier.id)}
                      className="p-2 rounded-full hover:bg-gray-100"
                    >
                      <MoreVertical className="h-4 w-4 text-gray-500" />
                    </button>

                    {openMenuId === supplier.id && (
                      <>
                        <div
                          className="fixed inset-0 z-10"
                          onClick={() => setOpenMenuId(null)}
                        />
                        <div className="absolute right-0 z-20 mt-2 w-48 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
                          <div className="py-1">
                            {onView && (
                              <button
                                onClick={() => handleAction(() => onView(supplier))}
                                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                              >
                                <Eye className="mr-3 h-4 w-4" />
                                查看详情
                              </button>
                            )}
                            {onEdit && (
                              <button
                                onClick={() => handleAction(() => onEdit(supplier))}
                                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                              >
                                <Edit className="mr-3 h-4 w-4" />
                                编辑
                              </button>
                            )}
                            {onStatusChange && supplier.status !== 'active' && (
                              <button
                                onClick={() => handleAction(() => onStatusChange(supplier, 'active' as SupplierStatus))}
                                className="flex items-center w-full px-4 py-2 text-sm text-green-700 hover:bg-gray-100"
                              >
                                <CheckCircle className="mr-3 h-4 w-4" />
                                激活
                              </button>
                            )}
                            {onStatusChange && supplier.status === 'active' && (
                              <button
                                onClick={() => handleAction(() => onStatusChange(supplier, 'suspended' as SupplierStatus))}
                                className="flex items-center w-full px-4 py-2 text-sm text-yellow-700 hover:bg-gray-100"
                              >
                                <Ban className="mr-3 h-4 w-4" />
                                暂停
                              </button>
                            )}
                            {onDelete && (
                              <button
                                onClick={() => handleAction(() => onDelete(supplier))}
                                className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-gray-100"
                              >
                                <Trash2 className="mr-3 h-4 w-4" />
                                删除
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

export default SuppliersTable;
