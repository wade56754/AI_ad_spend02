/**
 * FinanceTodoList Component
 *
 * 财务待办 + 低余额预警 - 从 FinancePage.tsx 提取
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Clock,
  AlertTriangle,
  ChevronRight,
} from 'lucide-react';
import {
  formatMoney,
  todoConfig,
  priorityLabels,
  priorityColors,
  type FinanceTodo,
  type LowBalanceAccount,
} from '../utils/financeHelpers';

interface FinanceTodoListProps {
  todos: FinanceTodo[];
  lowBalanceAccounts: LowBalanceAccount[];
  className?: string;
}

export function FinanceTodoList({ todos, lowBalanceAccounts, className }: FinanceTodoListProps) {
  const urgentCount = todos.filter(t => t.priority === 'high').length;

  return (
    <div className={`grid grid-cols-12 gap-6 ${className || ''}`} data-testid="finance-todo-list">
      {/* 财务待办 */}
      <div className="col-span-12 lg:col-span-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  财务待办
                </CardTitle>
                <CardDescription>需要处理的财务事项</CardDescription>
              </div>
              {urgentCount > 0 && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  {urgentCount} 个紧急
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {todos.map((todo) => {
                const config = todoConfig[todo.type];
                const Icon = config.icon;
                return (
                  <div key={todo.id} className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${config.bg}`}>
                      <Icon className={`h-5 w-5 ${config.color}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-gray-900">{todo.title}</p>
                        <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${priorityColors[todo.priority]}`}>
                          {priorityLabels[todo.priority]}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {todo.amount && (
                          <span className="text-sm text-gray-600">{formatMoney(todo.amount)}</span>
                        )}
                        <span className="text-xs text-gray-400">{todo.created_at}</span>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                );
              })}
              {todos.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  暂无待办事项
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 低余额预警 */}
      <div className="col-span-12 lg:col-span-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  余额预警
                </CardTitle>
                <CardDescription>余额不足的广告账户</CardDescription>
              </div>
              <Link href="/ad-accounts">
                <Button variant="ghost" size="sm">
                  查看全部 <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {lowBalanceAccounts.map((account) => (
                <div key={account.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${account.status === 'critical' ? 'bg-red-500' : 'bg-yellow-500'}`} />
                    <div>
                      <p className="font-medium text-gray-900">{account.name}</p>
                      <p className="text-xs text-gray-500">{account.platform}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-bold ${account.status === 'critical' ? 'text-red-600' : 'text-yellow-600'}`}>
                      ¥{(account.balance ?? 0).toLocaleString()}
                    </p>
                    <Link href="/topups">
                      <Button variant="link" size="sm" className="h-auto p-0 text-xs">
                        立即充值
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
              {lowBalanceAccounts.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  暂无余额预警
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default FinanceTodoList;
