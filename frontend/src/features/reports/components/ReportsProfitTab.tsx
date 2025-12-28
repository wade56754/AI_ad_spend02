/**
 * ReportsProfitTab Component
 *
 * 利润报表标签页 - 从 ReportsPage.tsx 提取
 */

'use client';

import React from 'react';
import { LoadingSpinner } from '@/modules/shared/components/feedback/LoadingSpinner';
import { formatCurrency, formatPercent } from '../utils/reportsHelpers';
import type { ProfitReportResponse } from '../types';

interface ReportsProfitTabProps {
  data: ProfitReportResponse | undefined;
  isLoading: boolean;
}

export function ReportsProfitTab({ data, isLoading }: ReportsProfitTabProps) {
  return (
    <div className="bg-white rounded-lg shadow" data-testid="reports-profit-tab">
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">利润报表</h3>
        {data?.meta && (
          <span className="text-sm text-gray-500">
            {data.meta.start_date} ~ {data.meta.end_date}
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
        </div>
      ) : data ? (
        <>
          {/* Summary */}
          <div className="px-6 py-4 bg-gray-50 border-b grid grid-cols-5 gap-4">
            <div>
              <div className="text-sm text-gray-500">总收入</div>
              <div className="text-lg font-bold text-green-600">
                {formatCurrency(parseFloat(data.summary.total_revenue))}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">总成本</div>
              <div className="text-lg font-bold text-red-600">
                {formatCurrency(parseFloat(data.summary.total_cost))}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">总利润</div>
              <div
                className={`text-lg font-bold ${
                  parseFloat(data.summary.total_profit) >= 0
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {formatCurrency(parseFloat(data.summary.total_profit))}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">利润率</div>
              <div
                className={`text-lg font-bold ${
                  (data.summary.profit_rate || 0) >= 0
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {formatPercent(data.summary.profit_rate)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">项目数</div>
              <div className="text-lg font-bold text-gray-900">
                {data.summary.project_count}
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    项目
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    收入
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    成本
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    利润
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    利润率
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.items.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        {item.project_name || '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-sm font-medium text-green-600">
                        {formatCurrency(item.revenue)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-sm font-medium text-red-600">
                        {formatCurrency(item.cost)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span
                        className={`text-sm font-medium ${
                          item.profit >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {formatCurrency(item.profit)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span
                        className={`text-sm ${
                          (item.profit_rate || 0) >= 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {formatPercent(item.profit_rate)}
                      </span>
                    </td>
                  </tr>
                ))}
                {data.items.length === 0 && (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-6 py-12 text-center text-gray-500"
                    >
                      暂无数据
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </div>
  );
}

export default ReportsProfitTab;
