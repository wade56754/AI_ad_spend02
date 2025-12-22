/**
 * ProfitTable Component
 *
 * Displays profit data in table format by dimension
 * SoT 对齐: BUSINESS_RULES.md v3.1
 */

'use client';

import React from 'react';
import { ArrowUpDown, TrendingUp, TrendingDown } from 'lucide-react';
import type {
  ProfitByProjectItem,
  ProfitByAccountItem,
  ProfitByChannelItem,
  ProfitDimension,
} from '../types';
import { PROFIT_DIMENSION_CONFIG } from '../types';

type ProfitItem = ProfitByProjectItem | ProfitByAccountItem | ProfitByChannelItem;

interface ProfitTableProps {
  data: ProfitItem[];
  dimension: ProfitDimension;
  loading?: boolean;
  onDimensionChange?: (dimension: ProfitDimension) => void;
  totalProfit?: number;
  overallMargin?: number;
}

export function ProfitTable({
  data,
  dimension,
  loading = false,
  onDimensionChange,
  totalProfit = 0,
  overallMargin = 0,
}: ProfitTableProps) {
  const [sortField, setSortField] = React.useState<string>('total_profit');
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>('desc');

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const sortedData = React.useMemo(() => {
    return [...data].sort((a, b) => {
      const aValue = (a as any)[sortField] || 0;
      const bValue = (b as any)[sortField] || 0;
      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    });
  }, [data, sortField, sortOrder]);

  const getNameField = (item: ProfitItem): string => {
    if ('project_name' in item) return item.project_name as string;
    if ('ad_account_name' in item) return item.ad_account_name as string;
    if ('channel_name' in item) return item.channel_name as string;
    return 'Unknown';
  };

  const getIdField = (item: ProfitItem): number => {
    if ('project_id' in item && !('ad_account_name' in item)) return item.project_id;
    if ('ad_account_id' in item) return item.ad_account_id;
    if ('channel_id' in item) return item.channel_id;
    return 0;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <div className="h-6 bg-gray-200 rounded w-1/4 animate-pulse"></div>
        </div>
        <div className="p-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-100 rounded mb-2 animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">利润明细</h3>
        {onDimensionChange && (
          <div className="flex gap-2">
            {Object.entries(PROFIT_DIMENSION_CONFIG)
              .filter(([key]) => key !== 'date')
              .map(([key, config]) => (
                <button
                  key={key}
                  onClick={() => onDimensionChange(key as ProfitDimension)}
                  className={`px-3 py-1 text-sm rounded-md ${
                    dimension === key
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {config.label}
                </button>
              ))}
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="px-4 py-3 bg-gray-50 border-b flex items-center gap-6">
        <div>
          <span className="text-sm text-gray-500">总利润: </span>
          <span className={`font-semibold ${totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(totalProfit)}
          </span>
        </div>
        <div>
          <span className="text-sm text-gray-500">整体利润率: </span>
          <span className={`font-semibold ${overallMargin >= 20 ? 'text-green-600' : overallMargin >= 10 ? 'text-yellow-600' : 'text-red-600'}`}>
            {overallMargin.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                名称
              </th>
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('total_conversions')}
              >
                <div className="flex items-center justify-end gap-1">
                  粉数
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('total_revenue')}
              >
                <div className="flex items-center justify-end gap-1">
                  收入
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('total_cost')}
              >
                <div className="flex items-center justify-end gap-1">
                  成本
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('total_profit')}
              >
                <div className="flex items-center justify-end gap-1">
                  利润
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('profit_margin')}
              >
                <div className="flex items-center justify-end gap-1">
                  利润率
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                  暂无数据
                </td>
              </tr>
            ) : (
              sortedData.map((item, index) => {
                const profit = item.total_profit;
                const margin = item.profit_margin;
                const isPositive = profit >= 0;

                return (
                  <tr key={getIdField(item)} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-500 w-6">
                          #{index + 1}
                        </span>
                        <span className="text-sm font-medium text-gray-900 ml-2">
                          {getNameField(item)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      {item.total_conversions.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-green-600">
                      {formatCurrency(item.total_revenue)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-red-600">
                      {formatCurrency(item.total_cost)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-1">
                        {isPositive ? (
                          <TrendingUp className="h-4 w-4 text-green-500" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-500" />
                        )}
                        <span
                          className={`text-sm font-medium ${
                            isPositive ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {formatCurrency(profit)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          margin >= 20
                            ? 'bg-green-100 text-green-800'
                            : margin >= 10
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {margin.toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ProfitTable;
