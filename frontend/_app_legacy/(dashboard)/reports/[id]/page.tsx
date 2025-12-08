'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  ArrowLeft,
  Download,
  Share,
  FileText,
  Calendar,
  Clock,
  User,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Eye,
  Edit,
  Trash2,
  Copy,
  RefreshCw,
  Filter,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle,
  PieChart,
  LineChart,
} from 'lucide-react';
import { toast } from 'sonner';

interface Report {
  id: string;
  title: string;
  description: string;
  type: 'daily' | 'weekly' | 'monthly' | 'custom';
  status: 'generating' | 'completed' | 'failed';
  createdAt: string;
  generatedAt: string;
  period: {
    startDate: string;
    endDate: string;
  };
  author: {
    id: string;
    name: string;
    email: string;
  };
  template: {
    id: string;
    name: string;
  };
  format: 'pdf' | 'excel' | 'csv';
  fileSize: number;
  downloadUrl: string;
  data: {
    summary: {
      totalSpend: number;
      totalConversions: number;
      totalImpressions: number;
      totalClicks: number;
      avgCTR: number;
      avgCPC: number;
      avgCPA: number;
      roas: number;
    };
    charts: Array<{
      id: string;
      type: 'line' | 'bar' | 'pie';
      title: string;
      data: any;
    }>;
    tables: Array<{
      id: string;
      title: string;
      headers: string[];
      rows: string[][];
    }>;
  };
  settings: {
    includeCharts: boolean;
    includeTables: boolean;
    includeRawData: boolean;
    compareWithPrevious: boolean;
  };
}

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [report, setReport] = useState<Report | null>(null);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [shareEmail, setShareEmail] = useState('');

  useEffect(() => {
    if (params.id) {
      fetchReport(params.id as string);
    }
  }, [params.id]);

  const fetchReport = async (reportId: string) => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      setReport({
        id: reportId,
        title: '2024年1月 Facebook广告投放月报',
        description: '包含本月所有Facebook广告账户的投放数据分析和趋势报告',
        type: 'monthly',
        status: 'completed',
        createdAt: '2024-02-01T09:00:00Z',
        generatedAt: '2024-02-01T09:15:00Z',
        period: {
          startDate: '2024-01-01',
          endDate: '2024-01-31',
        },
        author: {
          id: '1',
          name: '张经理',
          email: 'manager@example.com',
        },
        template: {
          id: 'monthly_facebook',
          name: 'Facebook月度报告模板',
        },
        format: 'pdf',
        fileSize: 2048576, // 2MB
        downloadUrl: '/api/reports/download/123.pdf',
        data: {
          summary: {
            totalSpend: 1250000,
            totalConversions: 8950,
            totalImpressions: 45600000,
            totalClicks: 125000,
            avgCTR: 0.27,
            avgCPC: 10,
            avgCPA: 140,
            roas: 3.2,
          },
          charts: [
            {
              id: 'spending_trend',
              type: 'line',
              title: '每日消费趋势',
              data: {},
            },
            {
              id: 'performance_comparison',
              type: 'bar',
              title: '账户表现对比',
              data: {},
            },
            {
              id: 'conversion_distribution',
              type: 'pie',
              title: '转化分布',
              data: {},
            },
          ],
          tables: [
            {
              id: 'account_summary',
              title: '账户汇总',
              headers: ['账户', '消费', '转化', 'ROI', '状态'],
              rows: [
                ['Facebook-Account-1', '¥450,000', '3,200', '3.8', '活跃'],
                ['Facebook-Account-2', '¥380,000', '2,850', '3.2', '活跃'],
                ['Facebook-Account-3', '¥420,000', '2,900', '3.1', '活跃'],
              ],
            },
            {
              id: 'campaign_performance',
              title: '广告系列表现',
              headers: ['系列名称', '消费', '展示', '点击', '转化', 'CTR', 'CPC'],
              rows: [
                ['春季促销', '¥180,000', '12,500,000', '35,000', '980', '0.28%', '¥5.14'],
                ['新品推广', '¥150,000', '10,200,000', '28,500', '750', '0.28%', '¥5.26'],
                ['品牌建设', '¥120,000', '8,500,000', '22,000', '520', '0.26%', '¥5.45'],
              ],
            },
          ],
        },
        settings: {
          includeCharts: true,
          includeTables: true,
          includeRawData: false,
          compareWithPrevious: true,
        },
      });
    } catch (error) {
      console.error('获取报告详情失败:', error);
      toast.error('获取报告详情失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'default';
      case 'generating': return 'secondary';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  const getStatusText = (status: string) => {
    const statusMap = {
      generating: '生成中',
      completed: '已完成',
      failed: '生成失败',
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  const getTypeText = (type: string) => {
    const typeMap = {
      daily: '日报',
      weekly: '周报',
      monthly: '月报',
      custom: '自定义',
    };
    return typeMap[type as keyof typeof typeMap] || type;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const downloadReport = async () => {
    if (!report) return;

    try {
      toast.info('正在下载报告...');
      // 实际下载逻辑
      const link = document.createElement('a');
      link.href = report.downloadUrl;
      link.download = `${report.title}.${report.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success('报告下载成功');
    } catch (error) {
      console.error('下载失败:', error);
      toast.error('报告下载失败');
    }
  };

  const shareReport = async () => {
    if (!report || !shareEmail) return;

    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      toast.success('报告分享成功');
      setShowShareDialog(false);
      setShareEmail('');
    } catch (error) {
      console.error('分享失败:', error);
      toast.error('报告分享失败');
    }
  };

  const regenerateReport = async () => {
    if (!report) return;

    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      setReport({
        ...report,
        status: 'generating',
      });

      toast.success('正在重新生成报告...');

      // 模拟生成完成
      setTimeout(() => {
        setReport(prev => prev ? {
          ...prev,
          status: 'completed',
          generatedAt: new Date().toISOString(),
        } : null);
        toast.success('报告重新生成完成');
      }, 3000);
    } catch (error) {
      console.error('重新生成失败:', error);
      toast.error('报告重新生成失败');
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            找不到指定的报告
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Link href="/reports">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回列表
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {report.title}
            </h1>
            <div className="flex items-center space-x-3 mt-2">
              <Badge variant={getStatusBadgeVariant(report.status)}>
                {getStatusText(report.status)}
              </Badge>
              <span className="text-sm text-gray-500">
                {getTypeText(report.type)}
              </span>
              <span className="text-sm text-gray-500">
                {report.format.toUpperCase()}
              </span>
              <span className="text-sm text-gray-500">
                {formatFileSize(report.fileSize)}
              </span>
            </div>
          </div>
        </div>
        <div className="flex space-x-3">
          {report.status === 'completed' && (
            <>
              <Button onClick={downloadReport}>
                <Download className="mr-2 h-4 w-4" />
                下载报告
              </Button>
              <Button variant="outline" onClick={() => setShowShareDialog(true)}>
                <Share className="mr-2 h-4 w-4" />
                分享
              </Button>
            </>
          )}
          <Button variant="outline" onClick={regenerateReport}>
            <RefreshCw className="mr-2 h-4 w-4" />
            重新生成
          </Button>
        </div>
      </div>

      {/* 报告信息 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-3">
              <Calendar className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  报告期间
                </p>
                <p className="text-sm text-gray-900 dark:text-white">
                  {report.period.startDate} 至 {report.period.endDate}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-3">
              <User className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  创建者
                </p>
                <p className="text-sm text-gray-900 dark:text-white">
                  {report.author.name} ({report.author.email})
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-3">
              <Clock className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  生成时间
                </p>
                <p className="text-sm text-gray-900 dark:text-white">
                  {new Date(report.generatedAt).toLocaleString('zh-CN')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 数据概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  总消费
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  ¥{(report.data.summary.totalSpend / 10000).toFixed(1)}万
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
                  总转化
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {report.data.summary.totalConversions.toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <BarChart3 className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  平均CTR
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {report.data.summary.avgCTR}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <PieChart className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  ROAS
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {report.data.summary.roas.toFixed(2)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="charts">图表</TabsTrigger>
          <TabsTrigger value="tables">数据表</TabsTrigger>
          <TabsTrigger value="settings">设置</TabsTrigger>
        </TabsList>

        {/* 概览 */}
        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>报告描述</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-400">
                {report.description}
              </p>

              <div className="mt-6 pt-6 border-t">
                <h4 className="text-lg font-medium mb-4">使用的模板</h4>
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="font-medium">{report.template.name}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    模板ID: {report.template.id}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 图表 */}
        <TabsContent value="charts">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {report.data.charts.map((chart) => (
              <Card key={chart.id}>
                <CardHeader>
                  <CardTitle>{chart.title}</CardTitle>
                  <CardDescription>
                    {chart.type === 'line' && '趋势分析图表'}
                    {chart.type === 'bar' && '对比分析图表'}
                    {chart.type === 'pie' && '占比分布图表'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-center">
                      {chart.type === 'line' && <LineChart className="h-12 w-12 text-gray-400 mx-auto mb-2" />}
                      {chart.type === 'bar' && <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />}
                      {chart.type === 'pie' && <PieChart className="h-12 w-12 text-gray-400 mx-auto mb-2" />}
                      <p className="text-sm text-gray-500">
                        图表预览 ({chart.type})
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* 数据表 */}
        <TabsContent value="tables">
          <div className="space-y-6">
            {report.data.tables.map((table) => (
              <Card key={table.id}>
                <CardHeader>
                  <CardTitle>{table.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b">
                          {table.headers.map((header, index) => (
                            <th key={index} className="text-left p-2 font-medium">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {table.rows.map((row, rowIndex) => (
                          <tr key={rowIndex} className="border-b">
                            {row.map((cell, cellIndex) => (
                              <td key={cellIndex} className="p-2">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* 设置 */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>报告设置</CardTitle>
              <CardDescription>
                当前报告的生成设置和配置
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">包含图表</p>
                    <p className="text-sm text-gray-600">在报告中包含可视化图表</p>
                  </div>
                  <Badge variant={report.settings.includeCharts ? 'default' : 'secondary'}>
                    {report.settings.includeCharts ? '已启用' : '已禁用'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">包含数据表</p>
                    <p className="text-sm text-gray-600">在报告中包含详细数据表格</p>
                  </div>
                  <Badge variant={report.settings.includeTables ? 'default' : 'secondary'}>
                    {report.settings.includeTables ? '已启用' : '已禁用'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">包含原始数据</p>
                    <p className="text-sm text-gray-600">在报告中包含原始数据文件</p>
                  </div>
                  <Badge variant={report.settings.includeRawData ? 'default' : 'secondary'}>
                    {report.settings.includeRawData ? '已启用' : '已禁用'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">对比上一期</p>
                    <p className="text-sm text-gray-600">与上一周期数据进行对比分析</p>
                  </div>
                  <Badge variant={report.settings.compareWithPrevious ? 'default' : 'secondary'}>
                    {report.settings.compareWithPrevious ? '已启用' : '已禁用'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 分享对话框 */}
      <Dialog open={showShareDialog} onOpenChange={setShowShareDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>分享报告</DialogTitle>
            <DialogDescription>
              输入邮箱地址分享此报告
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="space-y-2">
              <label htmlFor="share-email" className="text-sm font-medium">
                邮箱地址
              </label>
              <input
                id="share-email"
                type="email"
                value={shareEmail}
                onChange={(e) => setShareEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="输入邮箱地址"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowShareDialog(false)}>
              取消
            </Button>
            <Button onClick={shareReport} disabled={!shareEmail}>
              分享
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}