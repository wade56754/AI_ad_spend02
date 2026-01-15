/**
 * ReportsPerformanceTab Component
 *
 * 效果报表标签页 - 从 ReportsPage.tsx 提取
 */

'use client';

import React from 'react';
import { LoadingSpinner } from '@/modules/shared/components/feedback/LoadingSpinner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatCurrency } from '../utils/reportsHelpers';
import type { PerformanceReportResponse } from '../types';

interface ReportsPerformanceTabProps {
  data: PerformanceReportResponse | undefined;
  isLoading: boolean;
}

export function ReportsPerformanceTab({ data, isLoading }: ReportsPerformanceTabProps) {
  return (
    <div className="bg-white rounded-lg shadow" data-testid="reports-performance-tab">
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">效果报表</h3>
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
              <div className="text-sm text-gray-500">总消耗</div>
              <div className="text-lg font-bold text-gray-900">
                {formatCurrency(parseFloat(data.summary.total_spend))}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">总线索</div>
              <div className="text-lg font-bold text-gray-900">
                {data.summary.total_leads.toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">平均CPA</div>
              <div className="text-lg font-bold text-gray-900">
                {data.summary.avg_cpa ? formatCurrency(parseFloat(data.summary.avg_cpa)) : '-'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">项目数</div>
              <div className="text-lg font-bold text-gray-900">{data.summary.project_count}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">渠道数</div>
              <div className="text-lg font-bold text-gray-900">{data.summary.channel_count}</div>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <Table>
              <TableHeader className="bg-gray-50 border-b">
                <TableRow>
                  <TableHead className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    项目
                  </TableHead>
                  <TableHead className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    渠道
                  </TableHead>
                  <TableHead className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    消耗
                  </TableHead>
                  <TableHead className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    线索
                  </TableHead>
                  <TableHead className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    CPA
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-gray-200">
                {data.items.map((item, index) => (
                  <TableRow key={index} className="hover:bg-gray-50">
                    <TableCell className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        {item.project_name || '-'}
                      </span>
                    </TableCell>
                    <TableCell className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-500">{item.channel_name || '-'}</span>
                    </TableCell>
                    <TableCell className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(item.total_spend)}
                      </span>
                    </TableCell>
                    <TableCell className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-sm text-gray-900">
                        {item.total_leads.toLocaleString()}
                      </span>
                    </TableCell>
                    <TableCell className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-sm text-gray-900">
                        {item.cpa ? formatCurrency(item.cpa) : '-'}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
                {data.items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="px-6 py-12 text-center text-gray-500">
                      暂无数据
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </>
      ) : null}
    </div>
  );
}

export default ReportsPerformanceTab;
