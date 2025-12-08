"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AlertTriangle, Eye, Settings } from 'lucide-react';

interface AbnormalAccount {
  id: string;
  name: string;
  platform: string;
  issue: 'consumption' | 'performance' | 'budget' | 'status';
  severity: 'high' | 'medium' | 'low';
  lastActivity: string;
  status: 'active' | 'paused';
}

interface AbnormalAccountsTableProps {
  title?: string;
  accounts?: AbnormalAccount[];
  className?: string;
}

const mockAccounts: AbnormalAccount[] = [
  {
    id: '1',
    name: 'Facebook广告账户-001',
    platform: 'Facebook',
    issue: 'consumption',
    severity: 'high',
    lastActivity: '2小时前',
    status: 'active'
  },
  {
    id: '2',
    name: 'Instagram推广-045',
    platform: 'Instagram',
    issue: 'performance',
    severity: 'medium',
    lastActivity: '5小时前',
    status: 'active'
  },
  {
    id: '3',
    name: 'TikTok投放-112',
    platform: 'TikTok',
    issue: 'budget',
    severity: 'high',
    lastActivity: '1天前',
    status: 'paused'
  },
  {
    id: '4',
    name: 'Google Ads-789',
    platform: 'Google',
    issue: 'status',
    severity: 'low',
    lastActivity: '3天前',
    status: 'active'
  }
];

const getIssueLabel = (issue: string) => {
  switch (issue) {
    case 'consumption': return '消耗异常';
    case 'performance': return '性能下降';
    case 'budget': return '预算超限';
    case 'status': return '状态异常';
    default: return '未知异常';
  }
};

const getSeverityVariant = (severity: string) => {
  switch (severity) {
    case 'high': return 'destructive' as const;
    case 'medium': return 'secondary' as const;
    case 'low': return 'outline' as const;
    default: return 'outline' as const;
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'high': return 'text-red-600';
    case 'medium': return 'text-amber-600';
    case 'low': return 'text-blue-600';
    default: return 'text-gray-600';
  }
};

export function AbnormalAccountsTable({
  title = "异常账户",
  accounts = mockAccounts,
  className
}: AbnormalAccountsTableProps) {
  return (
    <Card className={`rounded-2xl shadow-sm border-slate-200/60 bg-white ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">
              {accounts.filter(a => a.severity === 'high').length} 高危
            </span>
            <Button variant="ghost" size="sm" className="text-xs hover:bg-slate-100">
              查看全部
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="space-y-1">
          {accounts.map((account) => (
            <div
              key={account.id}
              className="flex items-center justify-between px-5 py-2 hover:bg-slate-50 transition-colors cursor-pointer group"
            >
              {/* 账户信息 */}
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <div className={`w-1.5 h-1.5 rounded-full ${
                  account.severity === 'high' ? 'bg-red-500' :
                  account.severity === 'medium' ? 'bg-amber-500' : 'bg-slate-400'
                }`} />
                <div className="min-w-0">
                  <div className="font-medium text-sm text-slate-900 truncate group-hover:text-blue-600 transition-colors">
                    {account.name}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-slate-400">{account.platform}</span>
                    {account.status === 'paused' && (
                      <span className="text-xs text-slate-400">·</span>
                    )}
                    {account.status === 'paused' && (
                      <span className="text-xs text-slate-400">已暂停</span>
                    )}
                  </div>
                </div>
              </div>

              {/* 异常信息 */}
              <div className="text-right">
                <div className="text-sm text-slate-600">{getIssueLabel(account.issue)}</div>
                <div className="text-xs text-slate-400">{account.lastActivity}</div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}