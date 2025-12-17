'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Search,
  Filter,
  Download,
  Calendar,
  User,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  Eye,
  RefreshCw,
  FileText,
  Database,
  Settings,
  Trash2,
  DollarSign,
  Users,
  Clock,
  TrendingUp,
  Activity,
} from 'lucide-react';
import { toast } from 'sonner';

interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  userName: string;
  userEmail: string;
  userRole: string;
  action: string;
  resource: string;
  resourceId: string;
  ipAddress: string;
  userAgent: string;
  status: 'success' | 'failure' | 'warning';
  details: string;
  category: 'auth' | 'data' | 'system' | 'security' | 'finance';
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('7d');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, [dateRange]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      setLogs([
        {
          id: '1',
          timestamp: '2024-01-15T10:30:00Z',
          userId: '1',
          userName: '系统管理员',
          userEmail: 'admin@example.com',
          userRole: 'admin',
          action: 'LOGIN',
          resource: 'AUTH',
          resourceId: '',
          ipAddress: '192.168.1.100',
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
          status: 'success',
          details: '用户登录成功',
          category: 'auth',
        },
        {
          id: '2',
          timestamp: '2024-01-15T10:25:00Z',
          userId: '2',
          userName: '张经理',
          userEmail: 'manager@example.com',
          userRole: 'manager',
          action: 'CREATE',
          resource: 'PROJECT',
          resourceId: 'proj_123',
          ipAddress: '192.168.1.101',
          userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
          status: 'success',
          details: '创建新项目"Facebook Q1广告投放"',
          category: 'data',
        },
        {
          id: '3',
          timestamp: '2024-01-15T10:20:00Z',
          userId: '3',
          userName: '李广告主',
          userEmail: 'advertiser@example.com',
          userRole: 'advertiser',
          action: 'LOGIN_FAILED',
          resource: 'AUTH',
          resourceId: '',
          ipAddress: '192.168.1.102',
          userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
          status: 'failure',
          details: '登录失败：密码错误',
          category: 'security',
        },
        {
          id: '4',
          timestamp: '2024-01-15T10:15:00Z',
          userId: '4',
          userName: '王发布商',
          userEmail: 'publisher@example.com',
          userRole: 'publisher',
          action: 'UPDATE',
          resource: 'AD_ACCOUNT',
          resourceId: 'acc_456',
          ipAddress: '192.168.1.103',
          userAgent: 'Mozilla/5.0 (Android 12; SM-G991B)',
          status: 'success',
          details: '更新广告账户状态为"活跃"',
          category: 'data',
        },
        {
          id: '5',
          timestamp: '2024-01-15T10:10:00Z',
          userId: '5',
          userName: '赵财务',
          userEmail: 'finance@example.com',
          userRole: 'finance',
          action: 'APPROVE',
          resource: 'TOPUP',
          resourceId: 'top_789',
          ipAddress: '192.168.1.104',
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
          status: 'success',
          details: '批准充值申请 $10,000',
          category: 'finance',
        },
        {
          id: '6',
          timestamp: '2024-01-15T10:05:00Z',
          userId: '1',
          userName: '系统管理员',
          userEmail: 'admin@example.com',
          userRole: 'admin',
          action: 'SYSTEM_BACKUP',
          resource: 'SYSTEM',
          resourceId: '',
          ipAddress: '127.0.0.1',
          userAgent: 'System/Cron',
          status: 'success',
          details: '系统自动备份完成',
          category: 'system',
        },
      ]);
    } catch (error) {
      console.error('获取审计日志失败:', error);
      toast.error('获取审计日志失败');
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.userEmail.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.resource.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesAction = actionFilter === 'all' || log.action === actionFilter;
    const matchesStatus = statusFilter === 'all' || log.status === statusFilter;
    const matchesCategory = categoryFilter === 'all' || log.category === categoryFilter;

    return matchesSearch && matchesAction && matchesStatus && matchesCategory;
  });

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'success': return 'default';
      case 'failure': return 'destructive';
      case 'warning': return 'secondary';
      default: return 'outline';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'auth': return <Shield className="h-4 w-4" />;
      case 'data': return <Database className="h-4 w-4" />;
      case 'system': return <Settings className="h-4 w-4" />;
      case 'security': return <AlertTriangle className="h-4 w-4" />;
      case 'finance': return <DollarSign className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const getCategoryText = (category: string) => {
    const categoryMap = {
      auth: '认证',
      data: '数据',
      system: '系统',
      security: '安全',
      finance: '财务',
    };
    return categoryMap[category as keyof typeof categoryMap] || category;
  };

  const getStatusText = (status: string) => {
    const statusMap = {
      success: '成功',
      failure: '失败',
      warning: '警告',
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  const getActionText = (action: string) => {
    const actionMap = {
      LOGIN: '登录',
      LOGIN_FAILED: '登录失败',
      LOGOUT: '登出',
      CREATE: '创建',
      UPDATE: '更新',
      DELETE: '删除',
      APPROVE: '批准',
      REJECT: '拒绝',
      SYSTEM_BACKUP: '系统备份',
    };
    return actionMap[action as keyof typeof actionMap] || action;
  };

  const handleExportLogs = () => {
    toast.info('正在导出审计日志...');
    // 实际导出逻辑
  };

  const handleRefreshLogs = () => {
    fetchLogs();
    toast.success('审计日志已刷新');
  };

  const viewLogDetail = (log: AuditLog) => {
    setSelectedLog(log);
    setShowDetailDialog(true);
  };

  const getStatistics = () => {
    return {
      total: logs.length,
      success: logs.filter(l => l.status === 'success').length,
      failure: logs.filter(l => l.status === 'failure').length,
      warning: logs.filter(l => l.status === 'warning').length,
      today: logs.filter(l => {
        const logDate = new Date(l.timestamp).toDateString();
        const today = new Date().toDateString();
        return logDate === today;
      }).length,
    };
  };

  const stats = getStatistics();

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">审计日志</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            监控系统活动，追踪用户操作和系统事件
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" onClick={handleExportLogs}>
            <Download className="mr-2 h-4 w-4" />
            导出日志
          </Button>
          <Button variant="outline" onClick={handleRefreshLogs}>
            <RefreshCw className="mr-2 h-4 w-4" />
            刷新
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Activity className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  总日志数
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.total}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  成功操作
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.success}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  失败操作
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.failure}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  警告事件
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.warning}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Clock className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  今日日志
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.today}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 搜索和筛选 */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row space-y-4 lg:space-y-0 lg:space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="搜索用户、操作或资源..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={actionFilter} onValueChange={setActionFilter}>
              <SelectTrigger className="w-full lg:w-40">
                <SelectValue placeholder="操作筛选" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有操作</SelectItem>
                <SelectItem value="LOGIN">登录</SelectItem>
                <SelectItem value="CREATE">创建</SelectItem>
                <SelectItem value="UPDATE">更新</SelectItem>
                <SelectItem value="DELETE">删除</SelectItem>
                <SelectItem value="APPROVE">批准</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full lg:w-40">
                <SelectValue placeholder="状态筛选" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有状态</SelectItem>
                <SelectItem value="success">成功</SelectItem>
                <SelectItem value="failure">失败</SelectItem>
                <SelectItem value="warning">警告</SelectItem>
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full lg:w-40">
                <SelectValue placeholder="分类筛选" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有分类</SelectItem>
                <SelectItem value="auth">认证</SelectItem>
                <SelectItem value="data">数据</SelectItem>
                <SelectItem value="system">系统</SelectItem>
                <SelectItem value="security">安全</SelectItem>
                <SelectItem value="finance">财务</SelectItem>
              </SelectContent>
            </Select>
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-full lg:w-40">
                <SelectValue placeholder="时间范围" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1d">今天</SelectItem>
                <SelectItem value="7d">最近7天</SelectItem>
                <SelectItem value="30d">最近30天</SelectItem>
                <SelectItem value="90d">最近90天</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 日志列表 */}
      <Card>
        <CardHeader>
          <CardTitle>日志记录</CardTitle>
          <CardDescription>
            共 {filteredLogs.length} 条记录
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>时间</TableHead>
                    <TableHead>用户</TableHead>
                    <TableHead>操作</TableHead>
                    <TableHead>分类</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>IP地址</TableHead>
                    <TableHead>详情</TableHead>
                    <TableHead className="w-[100px]">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>
                        <div className="text-sm">
                          {new Date(log.timestamp).toLocaleDateString('zh-CN')}<br/>
                          {new Date(log.timestamp).toLocaleTimeString('zh-CN')}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{log.userName}</div>
                          <div className="text-sm text-gray-500">{log.userEmail}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{getActionText(log.action)}</div>
                          <div className="text-sm text-gray-500">{log.resource}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {getCategoryIcon(log.category)}
                          <span className="text-sm">{getCategoryText(log.category)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(log.status)}>
                          {getStatusText(log.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>{log.ipAddress}</TableCell>
                      <TableCell>
                        <div className="max-w-xs truncate text-sm">
                          {log.details}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => viewLogDetail(log)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 日志详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>日志详情</DialogTitle>
            <DialogDescription>
              查看详细的审计日志信息
            </DialogDescription>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">时间</Label>
                  <div className="text-sm">
                    {new Date(selectedLog.timestamp).toLocaleString('zh-CN')}
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium">状态</Label>
                  <div>
                    <Badge variant={getStatusBadgeVariant(selectedLog.status)}>
                      {getStatusText(selectedLog.status)}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium">用户</Label>
                  <div className="text-sm">
                    {selectedLog.userName} ({selectedLog.userEmail})
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium">用户角色</Label>
                  <div className="text-sm">{selectedLog.userRole}</div>
                </div>
                <div>
                  <Label className="text-sm font-medium">操作</Label>
                  <div className="text-sm">{getActionText(selectedLog.action)}</div>
                </div>
                <div>
                  <Label className="text-sm font-medium">资源</Label>
                  <div className="text-sm">{selectedLog.resource}</div>
                </div>
                <div>
                  <Label className="text-sm font-medium">IP地址</Label>
                  <div className="text-sm">{selectedLog.ipAddress}</div>
                </div>
                <div>
                  <Label className="text-sm font-medium">分类</Label>
                  <div className="flex items-center space-x-2">
                    {getCategoryIcon(selectedLog.category)}
                    <span className="text-sm">{getCategoryText(selectedLog.category)}</span>
                  </div>
                </div>
              </div>
              <div>
                <Label className="text-sm font-medium">用户代理</Label>
                <div className="text-sm p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  {selectedLog.userAgent}
                </div>
              </div>
              <div>
                <Label className="text-sm font-medium">详细信息</Label>
                <div className="text-sm p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  {selectedLog.details}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}