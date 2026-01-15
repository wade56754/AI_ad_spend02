/**
 * Ad Accounts Management Page V2.0
 *
 * Design Philosophy:
 * 1. Information Density - 一屏展示最多有效信息
 * 2. Quick Actions - 常用操作一键触达
 * 3. Smart Filters - 智能筛选，记住用户习惯
 * 4. Real-time Stats - 关键指标实时可见
 *
 * Author: Senior Frontend Engineer (10+ years)
 */

'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
  Search,
  Filter,
  Download,
  Upload,
  RefreshCw,
  MoreHorizontal,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  Users,
  DollarSign,
  BarChart3,
  ChevronDown,
  Eye,
  Pause,
  Play,
  Archive,
  Copy,
  ExternalLink,
  Settings2,
  Columns3,
  SlidersHorizontal,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

// ============ Types ============
interface AdAccount {
  id: number;
  name: string;
  platformId: string;
  accountType: string;
  platform: 'FB' | 'TK';
  supplier: string;
  buyer: string;
  region: string;
  status: 'active' | 'testing' | 'suspended' | 'dead' | 'new';
  todaySpend: number;
  yesterdaySpend: number;
  monthSpend: number;
  feeRate: number;
  lastUpdated: string;
  trend: number; // percentage change
}

// ============ Mock Data ============
const mockAccounts: AdAccount[] = [
  {
    id: 1,
    name: 'SONZDD-ADA+7-GX-324',
    platformId: '1138647123633445',
    accountType: '越南盾主题户',
    platform: 'FB',
    supplier: '海总&志诚三不限',
    buyer: 'YK',
    region: '印度',
    status: 'active',
    todaySpend: 245.32,
    yesterdaySpend: 198.45,
    monthSpend: 4521.8,
    feeRate: 0.1,
    lastUpdated: '2025-12-22 14:30',
    trend: 23.6,
  },
  {
    id: 2,
    name: 'Tencent IS Pte.Ltd +8 -089',
    platformId: '270468399386879',
    accountType: '美金户',
    platform: 'FB',
    supplier: 'B哥-fb三不限10➕1',
    buyer: 'LM',
    region: '印度',
    status: 'active',
    todaySpend: 419.48,
    yesterdaySpend: 803.74,
    monthSpend: 3009.58,
    feeRate: 0.11,
    lastUpdated: '2025-12-22 14:25',
    trend: -47.8,
  },
  {
    id: 3,
    name: 'PeakTime-489',
    platformId: '2456962661335328',
    accountType: '美金户',
    platform: 'FB',
    supplier: '凤凰&洛阳',
    buyer: 'YJ',
    region: '新加坡',
    status: 'testing',
    todaySpend: 15.95,
    yesterdaySpend: 0,
    monthSpend: 217.89,
    feeRate: 0.11,
    lastUpdated: '2025-12-22 13:45',
    trend: 100,
  },
  {
    id: 4,
    name: 'SHARK 003 MAX',
    platformId: '1258285486025414',
    accountType: '绑卡户',
    platform: 'FB',
    supplier: '印度户印尼企业户',
    buyer: 'LD',
    region: '印度',
    status: 'suspended',
    todaySpend: 0,
    yesterdaySpend: 2.14,
    monthSpend: 506.08,
    feeRate: 0.07,
    lastUpdated: '2025-12-22 09:00',
    trend: -100,
  },
  {
    id: 5,
    name: 'TK-Global-HK-001',
    platformId: '7892345678901234',
    accountType: 'TK海外主体全球户',
    platform: 'TK',
    supplier: '官方授权户',
    buyer: 'HY',
    region: '加拿大',
    status: 'active',
    todaySpend: 89.5,
    yesterdaySpend: 76.3,
    monthSpend: 1285.82,
    feeRate: 0.05,
    lastUpdated: '2025-12-22 14:28',
    trend: 17.3,
  },
];

// ============ Helper Functions ============
const formatCurrency = (value: number) => {
  if (value >= 10000) {
    return `$${(value / 1000).toFixed(1)}k`;
  }
  return `$${value.toFixed(2)}`;
};

const formatPercent = (value: number) => {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
};

const getStatusConfig = (status: AdAccount['status']) => {
  const configs = {
    active: {
      label: '投放中',
      color: 'bg-green-500',
      textColor: 'text-green-700',
      bgColor: 'bg-green-50',
    },
    testing: {
      label: '测试中',
      color: 'bg-blue-500',
      textColor: 'text-blue-700',
      bgColor: 'bg-blue-50',
    },
    suspended: {
      label: '已暂停',
      color: 'bg-yellow-500',
      textColor: 'text-yellow-700',
      bgColor: 'bg-yellow-50',
    },
    dead: { label: '死号', color: 'bg-red-500', textColor: 'text-red-700', bgColor: 'bg-red-50' },
    new: { label: '新建', color: 'bg-gray-400', textColor: 'text-gray-700', bgColor: 'bg-gray-50' },
  };
  return configs[status];
};

const getPlatformConfig = (platform: 'FB' | 'TK') => {
  return platform === 'FB'
    ? { label: 'Facebook', color: 'bg-blue-600' }
    : { label: 'TikTok', color: 'bg-black' };
};

// ============ Sub Components ============

// 顶部统计卡片 - 关键指标一眼可见
const StatsCards = ({ accounts }: { accounts: AdAccount[] }) => {
  const stats = useMemo(() => {
    const active = accounts.filter((a) => a.status === 'active').length;
    const todayTotal = accounts.reduce((sum, a) => sum + a.todaySpend, 0);
    const yesterdayTotal = accounts.reduce((sum, a) => sum + a.yesterdaySpend, 0);
    const monthTotal = accounts.reduce((sum, a) => sum + a.monthSpend, 0);
    const trend = yesterdayTotal > 0 ? ((todayTotal - yesterdayTotal) / yesterdayTotal) * 100 : 0;

    return { active, total: accounts.length, todayTotal, monthTotal, trend };
  }, [accounts]);

  return (
    <div className="grid grid-cols-4 gap-4">
      <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-xs font-medium">账户总数</p>
              <p className="text-2xl font-bold mt-1">{stats.total}</p>
              <p className="text-blue-100 text-xs mt-1">
                <span className="text-white font-medium">{stats.active}</span> 个投放中
              </p>
            </div>
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-xs font-medium">今日消耗</p>
              <p className="text-2xl font-bold mt-1">{formatCurrency(stats.todayTotal)}</p>
              <p className="text-green-100 text-xs mt-1 flex items-center gap-1">
                {stats.trend >= 0 ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                <span className={stats.trend >= 0 ? 'text-white' : 'text-green-200'}>
                  {formatPercent(stats.trend)}
                </span>
                vs 昨日
              </p>
            </div>
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-xs font-medium">本月消耗</p>
              <p className="text-2xl font-bold mt-1">{formatCurrency(stats.monthTotal)}</p>
              <p className="text-purple-100 text-xs mt-1">
                日均{' '}
                <span className="text-white font-medium">
                  {formatCurrency(stats.monthTotal / 22)}
                </span>
              </p>
            </div>
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-0">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-xs font-medium">平均费率</p>
              <p className="text-2xl font-bold mt-1">9.2%</p>
              <p className="text-orange-100 text-xs mt-1">
                手续费{' '}
                <span className="text-white font-medium">
                  {formatCurrency(stats.todayTotal * 0.092)}
                </span>
              </p>
            </div>
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// 智能筛选栏 - 高频筛选条件前置
const FilterBar = ({
  filters,
  onFilterChange,
  accounts,
}: {
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
  accounts: AdAccount[];
}) => {
  // 提取唯一值用于筛选
  const uniqueValues = useMemo(
    () => ({
      buyers: [...new Set(accounts.map((a) => a.buyer))],
      suppliers: [...new Set(accounts.map((a) => a.supplier))],
      accountTypes: [...new Set(accounts.map((a) => a.accountType))],
      regions: [...new Set(accounts.map((a) => a.region))],
    }),
    [accounts]
  );

  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* 搜索框 - 支持模糊搜索 */}
      <div className="relative flex-1 min-w-[240px] max-w-[320px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          placeholder="搜索账户名称、ID、投手..."
          className="pl-9 h-9 bg-white"
          value={filters.search || ''}
          onChange={(e) => onFilterChange('search', e.target.value)}
        />
      </div>

      {/* 快捷状态筛选 - Tab 式切换 */}
      <div className="flex items-center bg-gray-100 rounded-lg p-1">
        {['all', 'active', 'testing', 'suspended', 'dead'].map((status) => (
          <Button
            key={status}
            onClick={() => onFilterChange('status', status === 'all' ? '' : status)}
            variant="ghost"
            className={cn(
              'px-3 py-1.5 text-xs font-medium rounded-md transition-all',
              (filters.status || '') === (status === 'all' ? '' : status)
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            )}
          >
            {status === 'all' ? '全部' : getStatusConfig(status as AdAccount['status']).label}
          </Button>
        ))}
      </div>

      {/* 投手筛选 */}
      <Select
        value={filters.buyer || '__all__'}
        onValueChange={(v) => onFilterChange('buyer', v === '__all__' ? '' : v)}
      >
        <SelectTrigger className="w-[120px] h-9 bg-white">
          <SelectValue placeholder="投手" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部投手</SelectItem>
          {uniqueValues.buyers.map((buyer) => (
            <SelectItem key={buyer} value={buyer}>
              {buyer}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 代理商筛选 */}
      <Select
        value={filters.supplier || '__all__'}
        onValueChange={(v) => onFilterChange('supplier', v === '__all__' ? '' : v)}
      >
        <SelectTrigger className="w-[160px] h-9 bg-white">
          <SelectValue placeholder="代理商" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部代理商</SelectItem>
          {uniqueValues.suppliers.map((supplier) => (
            <SelectItem key={supplier} value={supplier}>
              {supplier}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 平台筛选 */}
      <Select
        value={filters.platform || '__all__'}
        onValueChange={(v) => onFilterChange('platform', v === '__all__' ? '' : v)}
      >
        <SelectTrigger className="w-[100px] h-9 bg-white">
          <SelectValue placeholder="平台" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部</SelectItem>
          <SelectItem value="FB">Facebook</SelectItem>
          <SelectItem value="TK">TikTok</SelectItem>
        </SelectContent>
      </Select>

      {/* 更多筛选 */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-9">
            <SlidersHorizontal className="w-4 h-4 mr-1" />
            更多
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-[200px]">
          <DropdownMenuLabel>账户类型</DropdownMenuLabel>
          {uniqueValues.accountTypes.map((type) => (
            <DropdownMenuCheckboxItem
              key={type}
              checked={filters.accountType === type}
              onCheckedChange={(checked) => onFilterChange('accountType', checked ? type : '')}
            >
              {type}
            </DropdownMenuCheckboxItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuLabel>地区</DropdownMenuLabel>
          {uniqueValues.regions.map((region) => (
            <DropdownMenuCheckboxItem
              key={region}
              checked={filters.region === region}
              onCheckedChange={(checked) => onFilterChange('region', checked ? region : '')}
            >
              {region}
            </DropdownMenuCheckboxItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 清除筛选 */}
      {Object.values(filters).some((v) => v) && (
        <Button
          variant="ghost"
          size="sm"
          className="h-9 text-gray-500"
          onClick={() => {
            Object.keys(filters).forEach((key) => onFilterChange(key, ''));
          }}
        >
          清除筛选
        </Button>
      )}
    </div>
  );
};

// 操作工具栏
const ActionBar = ({
  selectedCount,
  onRefresh,
  onExport,
  onImport,
}: {
  selectedCount: number;
  onRefresh: () => void;
  onExport: () => void;
  onImport: () => void;
}) => {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {selectedCount > 0 ? (
          <>
            <span className="text-sm text-gray-600">
              已选择 <span className="font-medium text-blue-600">{selectedCount}</span> 个账户
            </span>
            <Button variant="outline" size="sm">
              <Pause className="w-4 h-4 mr-1" />
              批量暂停
            </Button>
            <Button variant="outline" size="sm">
              <Users className="w-4 h-4 mr-1" />
              批量分配
            </Button>
            <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
              <Archive className="w-4 h-4 mr-1" />
              批量归档
            </Button>
          </>
        ) : (
          <span className="text-sm text-gray-500">提示：勾选账户可进行批量操作</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="sm" onClick={onRefresh}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>刷新数据</TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <Button variant="outline" size="sm" onClick={onImport}>
          <Upload className="w-4 h-4 mr-1" />
          导入
        </Button>

        <Button variant="outline" size="sm" onClick={onExport}>
          <Download className="w-4 h-4 mr-1" />
          导出
        </Button>

        {/* 列配置 */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <Columns3 className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>显示列</DropdownMenuLabel>
            <DropdownMenuCheckboxItem checked>账户名称</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked>投手</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked>代理商</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked>今日消耗</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked>本月消耗</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem>费率</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem>地区</DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

// 账户表格 - 高信息密度设计
const AccountTable = ({
  accounts,
  selectedIds,
  onSelectChange,
  onSelectAll,
}: {
  accounts: AdAccount[];
  selectedIds: Set<number>;
  onSelectChange: (id: number, checked: boolean) => void;
  onSelectAll: (checked: boolean) => void;
}) => {
  const allSelected = accounts.length > 0 && accounts.every((a) => selectedIds.has(a.id));
  const someSelected = accounts.some((a) => selectedIds.has(a.id));

  return (
    <div className="border rounded-lg overflow-hidden bg-white">
      <Table>
        <TableHeader>
          <TableRow className="bg-gray-50/80">
            <TableHead className="w-[40px]">
              <Checkbox checked={allSelected} onCheckedChange={onSelectAll} aria-label="全选" />
            </TableHead>
            <TableHead className="min-w-[280px]">账户信息</TableHead>
            <TableHead className="w-[80px]">投手</TableHead>
            <TableHead className="w-[160px]">代理商</TableHead>
            <TableHead className="w-[100px] text-right">今日消耗</TableHead>
            <TableHead className="w-[100px] text-right">本月消耗</TableHead>
            <TableHead className="w-[80px] text-center">状态</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {accounts.map((account) => {
            const statusConfig = getStatusConfig(account.status);
            const platformConfig = getPlatformConfig(account.platform);

            return (
              <TableRow
                key={account.id}
                className={cn(
                  'group hover:bg-blue-50/50 transition-colors',
                  selectedIds.has(account.id) && 'bg-blue-50'
                )}
              >
                <TableCell>
                  <Checkbox
                    checked={selectedIds.has(account.id)}
                    onCheckedChange={(checked) => onSelectChange(account.id, !!checked)}
                  />
                </TableCell>

                {/* 账户信息 - 紧凑但完整 */}
                <TableCell>
                  <div className="flex items-start gap-3">
                    {/* 平台标识 */}
                    <div
                      className={cn(
                        'w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0',
                        platformConfig.color
                      )}
                    >
                      {account.platform}
                    </div>

                    <div className="min-w-0 flex-1">
                      {/* 账户名称 - 可点击查看详情 */}
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900 truncate hover:text-blue-600 cursor-pointer">
                          {account.name}
                        </span>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span
                                role="button"
                                tabIndex={0}
                                className="opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                                onClick={() => navigator.clipboard.writeText(account.platformId)}
                                onKeyDown={(e) =>
                                  e.key === 'Enter' &&
                                  navigator.clipboard.writeText(account.platformId)
                                }
                              >
                                <Copy className="w-3 h-3 text-gray-400 hover:text-gray-600" />
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>复制账户ID</TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>

                      {/* 次要信息 */}
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-400 font-mono">
                          {account.platformId}
                        </span>
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                          {account.accountType}
                        </Badge>
                        <span className="text-xs text-gray-400">{account.region}</span>
                      </div>
                    </div>
                  </div>
                </TableCell>

                {/* 投手 */}
                <TableCell>
                  <div className="flex items-center gap-1.5">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-xs font-medium">
                      {account.buyer.charAt(0)}
                    </div>
                    <span className="text-sm font-medium">{account.buyer}</span>
                  </div>
                </TableCell>

                {/* 代理商 */}
                <TableCell>
                  <span
                    className="text-sm text-gray-600 truncate block max-w-[140px]"
                    title={account.supplier}
                  >
                    {account.supplier}
                  </span>
                  <span className="text-xs text-gray-400">
                    费率 {(account.feeRate * 100).toFixed(0)}%
                  </span>
                </TableCell>

                {/* 今日消耗 - 带趋势 */}
                <TableCell className="text-right">
                  <div className="flex flex-col items-end">
                    <span className="font-medium tabular-nums">
                      {formatCurrency(account.todaySpend)}
                    </span>
                    <div
                      className={cn(
                        'flex items-center gap-0.5 text-xs',
                        account.trend > 0
                          ? 'text-green-600'
                          : account.trend < 0
                            ? 'text-red-500'
                            : 'text-gray-400'
                      )}
                    >
                      {account.trend > 0 ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : account.trend < 0 ? (
                        <TrendingDown className="w-3 h-3" />
                      ) : null}
                      <span>{formatPercent(account.trend)}</span>
                    </div>
                  </div>
                </TableCell>

                {/* 本月消耗 */}
                <TableCell className="text-right">
                  <span className="font-medium tabular-nums">
                    {formatCurrency(account.monthSpend)}
                  </span>
                </TableCell>

                {/* 状态 */}
                <TableCell className="text-center">
                  <Badge
                    variant="secondary"
                    className={cn('text-xs', statusConfig.bgColor, statusConfig.textColor)}
                  >
                    <span className={cn('w-1.5 h-1.5 rounded-full mr-1.5', statusConfig.color)} />
                    {statusConfig.label}
                  </Badge>
                </TableCell>

                {/* 操作 */}
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Eye className="w-4 h-4 mr-2" />
                        查看详情
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <ExternalLink className="w-4 h-4 mr-2" />
                        在平台中打开
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      {account.status === 'active' ? (
                        <DropdownMenuItem>
                          <Pause className="w-4 h-4 mr-2" />
                          暂停投放
                        </DropdownMenuItem>
                      ) : account.status === 'suspended' ? (
                        <DropdownMenuItem>
                          <Play className="w-4 h-4 mr-2" />
                          恢复投放
                        </DropdownMenuItem>
                      ) : null}
                      <DropdownMenuItem>
                        <Users className="w-4 h-4 mr-2" />
                        重新分配
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-red-600">
                        <Archive className="w-4 h-4 mr-2" />
                        标记死号
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      {/* 表格底部 */}
      <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50/50">
        <span className="text-sm text-gray-500">共 {accounts.length} 个账户</span>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">每页</span>
          <Select defaultValue="20">
            <SelectTrigger className="w-[70px] h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10</SelectItem>
              <SelectItem value="20">20</SelectItem>
              <SelectItem value="50">50</SelectItem>
              <SelectItem value="100">100</SelectItem>
            </SelectContent>
          </Select>
          <span className="text-sm text-gray-500">条</span>
        </div>
      </div>
    </div>
  );
};

// ============ Main Component ============
export function AdAccountsPageV2() {
  // State
  const [accounts] = useState<AdAccount[]>(mockAccounts);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Filter handlers
  const handleFilterChange = useCallback((key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  // Filtered accounts - must be defined before handleSelectAll
  const filteredAccounts = useMemo(() => {
    return accounts.filter((account) => {
      if (filters.search) {
        const search = filters.search.toLowerCase();
        if (
          !account.name.toLowerCase().includes(search) &&
          !account.platformId.includes(search) &&
          !account.buyer.toLowerCase().includes(search)
        ) {
          return false;
        }
      }
      if (filters.status && account.status !== filters.status) return false;
      if (filters.buyer && account.buyer !== filters.buyer) return false;
      if (filters.supplier && account.supplier !== filters.supplier) return false;
      if (filters.platform && account.platform !== filters.platform) return false;
      if (filters.accountType && account.accountType !== filters.accountType) return false;
      if (filters.region && account.region !== filters.region) return false;
      return true;
    });
  }, [accounts, filters]);

  // Selection handlers
  const handleSelectChange = useCallback((id: number, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(
    (checked: boolean) => {
      if (checked) {
        setSelectedIds(new Set(filteredAccounts.map((a) => a.id)));
      } else {
        setSelectedIds(new Set());
      }
    },
    [filteredAccounts]
  );

  // Action handlers
  const handleRefresh = useCallback(() => {
    console.log('Refreshing...');
  }, []);

  const handleExport = useCallback(() => {
    console.log('Exporting...');
  }, []);

  const handleImport = useCallback(() => {
    console.log('Importing...');
  }, []);

  return (
    <div className="space-y-4">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">广告账号管理</h1>
          <p className="text-sm text-gray-500 mt-0.5">管理所有广告投放账户，监控消耗数据</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Clock className="w-3.5 h-3.5" />
          最后更新：2025-12-22 14:30
        </div>
      </div>

      {/* 统计卡片 */}
      <StatsCards accounts={accounts} />

      {/* 主内容区 */}
      <Card>
        <CardContent className="p-4 space-y-4">
          {/* 筛选栏 */}
          <FilterBar filters={filters} onFilterChange={handleFilterChange} accounts={accounts} />

          {/* 操作栏 */}
          <ActionBar
            selectedCount={selectedIds.size}
            onRefresh={handleRefresh}
            onExport={handleExport}
            onImport={handleImport}
          />

          {/* 账户表格 */}
          <AccountTable
            accounts={filteredAccounts}
            selectedIds={selectedIds}
            onSelectChange={handleSelectChange}
            onSelectAll={handleSelectAll}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export default AdAccountsPageV2;
