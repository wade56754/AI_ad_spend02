/**
 * FinanceTransactions Component
 *
 * 最近交易记录表格 - 从 FinancePage.tsx 提取
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { FileText, ChevronRight } from 'lucide-react';
import { formatMoney, transactionTypeConfig, type Transaction } from '../utils/financeHelpers';

interface FinanceTransactionsProps {
  transactions: Transaction[];
  className?: string;
}

export function FinanceTransactions({ transactions, className }: FinanceTransactionsProps) {
  return (
    <div className={className} data-testid="finance-transactions">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                最近交易
              </CardTitle>
              <CardDescription>最新的充值、消耗和结算记录</CardDescription>
            </div>
            <Link href="/reconciliation">
              <Button variant="ghost" size="sm">
                查看全部 <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-b">
                  <TableHead className="text-left py-3 px-4 font-medium text-gray-600">
                    时间
                  </TableHead>
                  <TableHead className="text-left py-3 px-4 font-medium text-gray-600">
                    类型
                  </TableHead>
                  <TableHead className="text-left py-3 px-4 font-medium text-gray-600">
                    账户/对象
                  </TableHead>
                  <TableHead className="text-right py-3 px-4 font-medium text-gray-600">
                    金额
                  </TableHead>
                  <TableHead className="text-left py-3 px-4 font-medium text-gray-600">
                    状态
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((tx) => {
                  const typeConfig = transactionTypeConfig[tx.type];
                  return (
                    <TableRow key={tx.id} className="border-b hover:bg-gray-50">
                      <TableCell className="py-3 px-4 text-sm text-gray-600">
                        {tx.created_at}
                      </TableCell>
                      <TableCell className="py-3 px-4">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${typeConfig.className}`}
                        >
                          {typeConfig.label}
                        </span>
                      </TableCell>
                      <TableCell className="py-3 px-4 text-sm font-medium text-gray-900">
                        {tx.account_name}
                      </TableCell>
                      <TableCell
                        className={`py-3 px-4 text-sm font-bold text-right ${
                          tx.amount >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {tx.amount >= 0 ? '+' : ''}
                        {formatMoney(tx.amount)}
                      </TableCell>
                      <TableCell className="py-3 px-4 text-sm text-gray-600">{tx.status}</TableCell>
                    </TableRow>
                  );
                })}
                {transactions.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                      暂无交易记录
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default FinanceTransactions;
