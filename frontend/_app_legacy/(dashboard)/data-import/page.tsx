'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Upload,
  Download,
  FileText,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Eye,
  Trash2,
  FileSpreadsheet,
  Database,
  Link,
  Settings,
  Play,
  Pause,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/page-header';
import { MetricCard } from '@/components/ui/MetricCard';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

// 数据导入任务类型
interface ImportJob {
  id: number;
  job_name: string;
  import_type: 'daily_report' | 'platform_bill' | 'account_data' | 'project_data';
  source_type: 'file_upload' | 'api_sync' | 'database_import';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  progress: number;
  total_records: number;
  processed_records: number;
  success_records: number;
  failed_records: number;
  file_name?: string;
  file_size?: number;
  error_message?: string;
  created_by: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  configuration: {
    has_header: boolean;
    delimiter: string;
    encoding: string;
    mapping: Record<string, string>;
  };
}

interface DataPreview {
  headers: string[];
  rows: string[][];
  total_rows: number;
}

interface ImportTemplate {
  id: number;
  name: string;
  description: string;
  import_type: string;
  file_format: string;
  required_columns: string[];
  optional_columns: string[];
  sample_data: string[][];
  download_url: string;
}

// 模拟数据
const mockImportJobs: ImportJob[] = [
  {
    id: 1,
    job_name: '2024年11月Facebook账单导入',
    import_type: 'platform_bill',
    source_type: 'file_upload',
    status: 'completed',
    progress: 100,
    total_records: 1250,
    processed_records: 1250,
    success_records: 1245,
    failed_records: 5,
    file_name: 'facebook_bill_202411.xlsx',
    file_size: 2048000,
    created_by: '财务部-张三',
    created_at: '2024-11-13T09:00:00Z',
    started_at: '2024-11-13T09:05:00Z',
    completed_at: '2024-11-13T09:15:00Z',
    configuration: {
      has_header: true,
      delimiter: ',',
      encoding: 'UTF-8',
      mapping: {
        'Date': 'date',
        'Account ID': 'account_id',
        'Spend': 'spend',
        'Impressions': 'impressions',
      },
    },
  },
  {
    id: 2,
    job_name: 'TikTok日报数据批量导入',
    import_type: 'daily_report',
    source_type: 'file_upload',
    status: 'running',
    progress: 65,
    total_records: 890,
    processed_records: 578,
    success_records: 575,
    failed_records: 3,
    file_name: 'tiktok_daily_reports.zip',
    file_size: 1024000,
    created_by: '数据部-李四',
    created_at: '2024-11-13T10:30:00Z',
    started_at: '2024-11-13T10:35:00Z',
    configuration: {
      has_header: true,
      delimiter: ',',
      encoding: 'UTF-8',
      mapping: {
        'Date': 'date',
        'Account': 'account_name',
        'Cost': 'cost',
        'Conversions': 'conversions',
      },
    },
  },
  {
    id: 3,
    job_name: 'Google Ads API同步',
    import_type: 'platform_bill',
    source_type: 'api_sync',
    status: 'failed',
    progress: 25,
    total_records: 500,
    processed_records: 125,
    success_records: 120,
    failed_records: 5,
    created_by: '技术部-王五',
    created_at: '2024-11-13T11:00:00Z',
    started_at: '2024-11-13T11:05:00Z',
    completed_at: '2024-11-13T11:15:00Z',
    error_message: 'API认证失败，请检查访问令牌',
    configuration: {
      has_header: true,
      delimiter: ',',
      encoding: 'UTF-8',
      mapping: {},
    },
  },
];

const mockTemplates: ImportTemplate[] = [
  {
    id: 1,
    name: '日报导入模板',
    description: '用于导入每日广告投放数据报告',
    import_type: 'daily_report',
    file_format: 'xlsx',
    required_columns: ['Date', 'Account ID', 'Account Name', 'Spend', 'Conversions'],
    optional_columns: ['Impressions', 'Clicks', 'CTR', 'CPC'],
    sample_data: [
      ['2024-11-13', '123456789', 'Test Account', '100.50', '25'],
      ['2024-11-13', '987654321', 'Another Account', '75.25', '18'],
    ],
    download_url: '/templates/daily_report_template.xlsx',
  },
  {
    id: 2,
    name: '平台账单导入模板',
    description: '用于导入平台官方账单数据',
    import_type: 'platform_bill',
    file_format: 'csv',
    required_columns: ['Date', 'Account ID', 'Cost', 'Currency'],
    optional_columns: ['Campaign', 'Ad Group', 'Impressions'],
    sample_data: [
      ['2024-11-13', '123456789', '150.75', 'USD'],
      ['2024-11-13', '987654321', '89.50', 'USD'],
    ],
    download_url: '/templates/platform_bill_template.csv',
  },
];

export default function DataImportPage() {
  const [importJobs, setImportJobs] = useState<ImportJob[]>(mockImportJobs);
  const [templates, setTemplates] = useState<ImportTemplate[]>(mockTemplates);
  const [loading, setLoading] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<DataPreview | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [importConfig, setImportConfig] = useState({
    import_type: 'daily_report',
    has_header: true,
    delimiter: ',',
    encoding: 'UTF-8',
    mapping: {} as Record<string, string>,
  });

  // 统计数据
  const stats = {
    total_jobs: importJobs.length,
    running_jobs: importJobs.filter(job => job.status === 'running').length,
    completed_jobs: importJobs.filter(job => job.status === 'completed').length,
    failed_jobs: importJobs.filter(job => job.status === 'failed').length,
    total_records: importJobs.reduce((sum, job) => sum + job.total_records, 0),
    success_rate: importJobs.length > 0
      ? (importJobs.reduce((sum, job) => sum + job.success_records, 0) /
         importJobs.reduce((sum, job) => sum + job.processed_records, 0)) * 100
      : 0,
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: '等待中', color: 'secondary' as const, icon: Clock },
      running: { label: '运行中', color: 'info' as const, icon: RefreshCw },
      completed: { label: '已完成', color: 'success' as const, icon: CheckCircle },
      failed: { label: '失败', color: 'destructive' as const, icon: XCircle },
      paused: { label: '已暂停', color: 'warning' as const, icon: Pause },
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    const Icon = config.icon;

    return (
      <Badge variant={config.color} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const getImportTypeLabel = (type: string) => {
    const typeLabels = {
      daily_report: '日报导入',
      platform_bill: '平台账单',
      account_data: '账户数据',
      project_data: '项目数据',
    };
    return typeLabels[type as keyof typeof typeLabels] || type;
  };

  const getSourceTypeIcon = (type: string) => {
    const icons = {
      file_upload: Upload,
      api_sync: Link,
      database_import: Database,
    };
    const Icon = icons[type as keyof typeof icons] || FileText;
    return <Icon className="h-4 w-4" />;
  };

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // 模拟文件预览
      const mockPreview: DataPreview = {
        headers: ['Date', 'Account ID', 'Account Name', 'Spend', 'Conversions'],
        rows: [
          ['2024-11-13', '123456789', 'Test Account', '100.50', '25'],
          ['2024-11-13', '987654321', 'Another Account', '75.25', '18'],
          ['2024-11-13', '456789123', 'Third Account', '120.00', '32'],
        ],
        total_rows: 150,
      };
      setPreviewData(mockPreview);
    }
  }, []);

  const handleStartImport = async () => {
    if (!selectedFile) {
      alert('请选择要导入的文件');
      return;
    }

    setLoading(true);
    try {
      // 模拟导入过程
      const newJob: ImportJob = {
        id: Date.now(),
        job_name: selectedFile.name,
        import_type: importConfig.import_type as any,
        source_type: 'file_upload',
        status: 'pending',
        progress: 0,
        total_records: 100,
        processed_records: 0,
        success_records: 0,
        failed_records: 0,
        file_name: selectedFile.name,
        file_size: selectedFile.size,
        created_by: '当前用户',
        created_at: new Date().toISOString(),
        configuration: importConfig,
      };

      setImportJobs([newJob, ...importJobs]);
      setShowUploadDialog(false);
      setSelectedFile(null);
      setPreviewData(null);
    } finally {
      setLoading(false);
    }
  };

  const handlePauseJob = async (jobId: number) => {
    setImportJobs(importJobs.map(job =>
      job.id === jobId
        ? { ...job, status: 'paused' as const }
        : job
    ));
  };

  const handleResumeJob = async (jobId: number) => {
    setImportJobs(importJobs.map(job =>
      job.id === jobId
        ? { ...job, status: 'running' as const }
        : job
    ));
  };

  const handleDeleteJob = async (jobId: number) => {
    if (confirm('确定要删除这个导入任务吗？')) {
      setImportJobs(importJobs.filter(job => job.id !== jobId));
    }
  };

  const handleDownloadTemplate = (template: ImportTemplate) => {
    // 模拟模板下载
    const link = document.createElement('a');
    link.href = template.download_url;
    link.download = `${template.name}.${template.file_format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <PageHeader
        title="数据导入工具"
        subtitle="支持多种数据源的批量导入，包括日报、平台账单、账户数据等"
        actions={
          <Button onClick={() => setShowUploadDialog(true)}>
            <Upload className="h-4 w-4 mr-2" />
            新建导入任务
          </Button>
        }
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="总导入任务"
          value={stats.total_jobs}
          description="全部导入任务数"
          color="primary"
          icon={FileText}
          size="sm"
        />
        <MetricCard
          title="运行中"
          value={stats.running_jobs}
          description="正在执行的任务"
          color="info"
          icon={RefreshCw}
          size="sm"
        />
        <MetricCard
          title="已完成"
          value={stats.completed_jobs}
          description="成功完成的任务"
          color="success"
          icon={CheckCircle}
          size="sm"
        />
        <MetricCard
          title="失败任务"
          value={stats.failed_jobs}
          description="需要处理的任务"
          color="destructive"
          icon={XCircle}
          size="sm"
        />
        <MetricCard
          title="总记录数"
          value={stats.total_records.toLocaleString()}
          description="已处理的记录数"
          color="warning"
          icon={Database}
          size="sm"
        />
      </div>

      {/* 导入模板 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            导入模板
          </CardTitle>
          <CardDescription>
            下载标准模板，按照格式准备数据以确保导入成功
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <Card key={template.id} className="border-dashed">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    <div>
                      <h3 className="font-medium">{template.name}</h3>
                      <p className="text-sm text-gray-600">{template.description}</p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Badge variant="outline">{template.file_format.toUpperCase()}</Badge>
                      <span>{template.required_columns.length} 个必填字段</span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadTemplate(template)}
                      className="w-full"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      下载模板
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 导入任务列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            导入任务管理
          </CardTitle>
          <CardDescription>
            查看和管理所有数据导入任务的执行状态和结果
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务名称</TableHead>
                  <TableHead>导入类型</TableHead>
                  <TableHead>数据源</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>进度</TableHead>
                  <TableHead>处理结果</TableHead>
                  <TableHead>创建人</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {importJobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium">{job.job_name}</div>
                        {job.file_name && (
                          <div className="text-sm text-gray-500">{job.file_name}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getImportTypeLabel(job.import_type)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getSourceTypeIcon(job.source_type)}
                        <span className="text-sm">
                          {job.source_type === 'file_upload' ? '文件上传' :
                           job.source_type === 'api_sync' ? 'API同步' : '数据库导入'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(job.status)}</TableCell>
                    <TableCell>
                      <div className="space-y-2 min-w-[120px]">
                        <div className="flex justify-between text-sm">
                          <span>{job.processed_records}/{job.total_records}</span>
                          <span>{job.progress}%</span>
                        </div>
                        <Progress value={job.progress} className="h-2" />
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm space-y-1">
                        <div className="flex items-center gap-1">
                          <CheckCircle className="h-3 w-3 text-green-500" />
                          <span>成功: {job.success_records}</span>
                        </div>
                        {job.failed_records > 0 && (
                          <div className="flex items-center gap-1">
                            <XCircle className="h-3 w-3 text-red-500" />
                            <span>失败: {job.failed_records}</span>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">{job.created_by}</TableCell>
                    <TableCell className="text-sm">
                      {format(new Date(job.created_at), 'MM/dd HH:mm')}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {job.status === 'running' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handlePauseJob(job.id)}
                          >
                            <Pause className="h-4 w-4" />
                          </Button>
                        )}
                        {job.status === 'paused' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleResumeJob(job.id)}
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        )}
                        {job.file_name && (
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteJob(job.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* 上传对话框 */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建新的导入任务</DialogTitle>
            <DialogDescription>
              选择文件并配置导入参数来创建新的数据导入任务
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* 文件选择 */}
            <div className="space-y-2">
              <Label htmlFor="file">选择文件</Label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div className="mt-2">
                  <label htmlFor="file" className="cursor-pointer">
                    <span className="text-blue-600 hover:text-blue-500">
                      点击上传文件
                    </span>
                    <Input
                      id="file"
                      type="file"
                      className="hidden"
                      accept=".xlsx,.xls,.csv,.zip"
                      onChange={handleFileSelect}
                    />
                  </label>
                  <p className="text-gray-500">或拖拽文件到此处</p>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  支持 Excel、CSV、ZIP 格式，最大 50MB
                </p>
              </div>
              {selectedFile && (
                <div className="mt-2 p-2 bg-gray-50 rounded">
                  <p className="text-sm">已选择: {selectedFile.name}</p>
                  <p className="text-xs text-gray-500">
                    大小: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              )}
            </div>

            {/* 导入配置 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="importType">导入类型</Label>
                <Select
                  value={importConfig.import_type}
                  onValueChange={(value) => setImportConfig({
                    ...importConfig,
                    import_type: value,
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily_report">日报导入</SelectItem>
                    <SelectItem value="platform_bill">平台账单</SelectItem>
                    <SelectItem value="account_data">账户数据</SelectItem>
                    <SelectItem value="project_data">项目数据</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="encoding">文件编码</Label>
                <Select
                  value={importConfig.encoding}
                  onValueChange={(value) => setImportConfig({
                    ...importConfig,
                    encoding: value,
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="UTF-8">UTF-8</SelectItem>
                    <SelectItem value="GBK">GBK</SelectItem>
                    <SelectItem value="GB2312">GB2312</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="hasHeader"
                checked={importConfig.has_header}
                onChange={(e) => setImportConfig({
                  ...importConfig,
                  has_header: e.target.checked,
                })}
              />
              <Label htmlFor="hasHeader">文件包含标题行</Label>
            </div>

            {/* 数据预览 */}
            {previewData && (
              <div className="space-y-2">
                <Label>数据预览 (前3行)</Label>
                <div className="border rounded-lg overflow-hidden">
                  <div className="max-h-48 overflow-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          {previewData.headers.map((header, index) => (
                            <th key={index} className="px-2 py-1 text-left border-b">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {previewData.rows.map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {row.map((cell, cellIndex) => (
                              <td key={cellIndex} className="px-2 py-1 border-b">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="bg-gray-50 px-2 py-1 text-xs text-gray-500">
                    共 {previewData.total_rows} 行数据
                  </div>
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUploadDialog(false)}>
              取消
            </Button>
            <Button onClick={handleStartImport} disabled={!selectedFile || loading}>
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  处理中...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  开始导入
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}