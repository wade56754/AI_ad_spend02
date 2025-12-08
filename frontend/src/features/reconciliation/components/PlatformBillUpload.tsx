"use client";

import React, { useState, useCallback } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Upload,
  FileSpreadsheet,
  FileText,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Download,
  Eye,
  Trash2,
  Clock,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";

// 类型定义
interface UploadedFile {
  id: string;
  filename: string;
  original_name: string;
  platform: string;
  file_size: number;
  upload_time: string;
  status: "uploading" | "processing" | "completed" | "failed";
  records_count?: number;
  valid_records?: number;
  invalid_records?: number;
  error_message?: string;
  preview_data?: Array<{
    account_id: string;
    account_name: string;
    platform_spend: number;
    currency: string;
    date: string;
  }>;
}

interface PlatformBillUploadProps {
  open: boolean;
  onClose: () => void;
  batchId: number;
  onUploadSuccess?: () => void;
}

// 平台配置
const platformConfigs = {
  facebook: {
    name: "Facebook",
    file_types: [".csv", ".xlsx", ".xls"],
    template_url: "/templates/facebook-bill-template.xlsx",
    required_fields: ["account_id", "account_name", "platform_spend", "currency", "date"],
    description: "支持Facebook广告管理器导出的账单文件",
  },
  tiktok: {
    name: "TikTok",
    file_types: [".csv", ".xlsx", ".xls"],
    template_url: "/templates/tiktok-bill-template.xlsx",
    required_fields: ["account_id", "account_name", "platform_spend", "currency", "date"],
    description: "支持TikTok广告平台导出的账单文件",
  },
  google: {
    name: "Google Ads",
    file_types: [".csv", ".xlsx", ".xls"],
    template_url: "/templates/google-ads-bill-template.xlsx",
    required_fields: ["account_id", "account_name", "platform_spend", "currency", "date"],
    description: "支持Google Ads导出的账单文件",
  },
  twitter: {
    name: "Twitter Ads",
    file_types: [".csv", ".xlsx", ".xls"],
    template_url: "/templates/twitter-ads-bill-template.xlsx",
    required_fields: ["account_id", "account_name", "platform_spend", "currency", "date"],
    description: "支持Twitter Ads导出的账单文件",
  },
};

export function PlatformBillUpload({
  open,
  onClose,
  batchId,
  onUploadSuccess,
}: PlatformBillUploadProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<string>("");
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // 处理文件选择
  const handleFileSelect = useCallback(async (files: FileList) => {
    if (!selectedPlatform) {
      toast.error("请先选择平台");
      return;
    }

    const platformConfig = platformConfigs[selectedPlatform as keyof typeof platformConfigs];

    // 验证文件类型
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileExtension = "." + file.name.split('.').pop()?.toLowerCase();

      if (!platformConfig.file_types.includes(fileExtension)) {
        toast.error(`文件 ${file.name} 格式不支持，请上传 ${platformConfig.file_types.join(", ")} 格式的文件`);
        return;
      }

      // 文件大小限制 (10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast.error(`文件 ${file.name} 大小超过10MB限制`);
        return;
      }
    }

    // 开始上传
    for (let i = 0; i < files.length; i++) {
      await uploadFile(files[i]);
    }
  }, [selectedPlatform]);

  // 上传单个文件
  const uploadFile = async (file: File) => {
    const fileId = Date.now().toString() + Math.random().toString(36).substr(2, 9);

    // 创建文件记录
    const fileRecord: UploadedFile = {
      id: fileId,
      filename: `${selectedPlatform}_${file.name}`,
      original_name: file.name,
      platform: selectedPlatform,
      file_size: file.size,
      upload_time: new Date().toISOString(),
      status: "uploading",
    };

    setUploadedFiles(prev => [...prev, fileRecord]);

    try {
      // 创建FormData
      const formData = new FormData();
      formData.append("file", file);
      formData.append("platform", selectedPlatform);
      formData.append("batch_id", batchId.toString());

      // 上传文件
      const response = await fetch("/api/v1/reconciliation/upload-platform-bill", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();

        // 更新文件记录
        setUploadedFiles(prev => prev.map(f =>
          f.id === fileId
            ? {
                ...f,
                status: "completed",
                records_count: result.data.records_count,
                valid_records: result.data.valid_records,
                invalid_records: result.data.invalid_records,
                preview_data: result.data.preview_data,
              }
            : f
        ));

        toast.success(`文件 ${file.name} 上传成功`);
      } else {
        const error = await response.json();
        throw new Error(error.message || "上传失败");
      }
    } catch (error) {
      console.error("文件上传错误:", error);
      setUploadedFiles(prev => prev.map(f =>
        f.id === fileId
          ? { ...f, status: "failed", error_message: error instanceof Error ? error.message : "上传失败" }
          : f
      ));
      toast.error(`文件 ${file.name} 上传失败`);
    }
  };

  // 拖拽处理
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  }, [handleFileSelect]);

  // 删除文件
  const handleDeleteFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    toast.success("文件已移除");
  };

  // 下载模板
  const handleDownloadTemplate = async () => {
    if (!selectedPlatform) {
      toast.error("请先选择平台");
      return;
    }

    try {
      const response = await fetch(`/api/v1/reconciliation/templates/${selectedPlatform}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${selectedPlatform}-bill-template.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("模板下载成功");
      }
    } catch (error) {
      toast.error("模板下载失败");
    }
  };

  // 重新上传
  const handleReupload = async (file: UploadedFile) => {
    // 这里需要重新选择文件，简化处理
    const input = document.createElement("input");
    input.type = "file";
    input.accept = platformConfigs[file.platform as keyof typeof platformConfigs].file_types.join(",");
    input.onchange = async (e) => {
      const files = (e.target as HTMLInputElement).files;
      if (files && files.length > 0) {
        await handleFileSelect(files);
        handleDeleteFile(file.id);
      }
    };
    input.click();
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "uploading":
        return <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />;
      case "processing":
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "failed":
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case "uploading": return "上传中";
      case "processing": return "处理中";
      case "completed": return "已完成";
      case "failed": return "失败";
      default: return "未知";
    }
  };

  // 重置状态
  const handleClose = () => {
    setSelectedPlatform("");
    setUploadedFiles([]);
    setDragActive(false);
    onClose();
    if (onUploadSuccess && uploadedFiles.some(f => f.status === "completed")) {
      onUploadSuccess();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            上传平台账单
          </DialogTitle>
          <DialogDescription>
            上传各广告平台的账单文件，用于对账分析
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 平台选择 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">选择平台</CardTitle>
              <CardDescription>选择要上传账单的广告平台</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(platformConfigs).map(([key, config]) => (
                  <div
                    key={key}
                    className={`cursor-pointer rounded-lg border-2 p-4 transition-all ${
                      selectedPlatform === key
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                    onClick={() => setSelectedPlatform(key)}
                  >
                    <div className="font-medium">{config.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {config.file_types.join(", ")}
                    </div>
                  </div>
                ))}
              </div>

              {selectedPlatform && (
                <Alert className="mt-4">
                  <FileText className="h-4 w-4" />
                  <AlertDescription>
                    {platformConfigs[selectedPlatform as keyof typeof platformConfigs].description}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* 文件上传区域 */}
          {selectedPlatform && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center justify-between">
                  上传账单文件
                  <Button variant="outline" size="sm" onClick={handleDownloadTemplate}>
                    <Download className="w-4 h-4 mr-2" />
                    下载模板
                  </Button>
                </CardTitle>
                <CardDescription>
                  拖拽文件到此处或点击选择文件上传
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-300 hover:border-gray-400"
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <div className="text-lg font-medium text-gray-900 mb-2">
                    拖拽文件到此处或点击上传
                  </div>
                  <p className="text-sm text-gray-500 mb-4">
                    支持格式: {platformConfigs[selectedPlatform as keyof typeof platformConfigs].file_types.join(", ")}
                  </p>
                  <Button asChild>
                    <label className="cursor-pointer">
                      <input
                        type="file"
                        className="hidden"
                        multiple
                        accept={platformConfigs[selectedPlatform as keyof typeof platformConfigs].file_types.join(",")}
                        onChange={(e) => e.target.files && handleFileSelect(e.target.files)}
                      />
                      选择文件
                    </label>
                  </Button>
                </div>

                {/* 上传进度 */}
                {uploadedFiles.length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-medium mb-4">上传文件列表</h4>
                    <div className="space-y-4">
                      {uploadedFiles.map((file) => (
                        <div key={file.id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <FileSpreadsheet className="w-4 h-4 text-gray-500" />
                                <span className="font-medium">{file.original_name}</span>
                                <Badge variant="outline">{file.platform}</Badge>
                              </div>
                              <div className="text-sm text-gray-500 mt-1">
                                {formatFileSize(file.file_size)} • {format(new Date(file.upload_time), "MM/dd HH:mm")}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="flex items-center gap-1">
                                {getStatusIcon(file.status)}
                                <span className="text-sm">{getStatusText(file.status)}</span>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteFile(file.id)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>

                          {/* 进度条 */}
                          {file.status === "uploading" && (
                            <Progress value={50} className="mb-2" />
                          )}

                          {/* 错误信息 */}
                          {file.status === "failed" && file.error_message && (
                            <Alert className="mt-2">
                              <AlertTriangle className="h-4 w-4" />
                              <AlertDescription>{file.error_message}</AlertDescription>
                            </Alert>
                          )}

                          {/* 处理结果 */}
                          {file.status === "completed" && file.records_count && (
                            <div className="mt-2 text-sm text-gray-600">
                              共 {file.records_count} 条记录，
                              有效 {file.valid_records} 条，
                              无效 {file.invalid_records} 条
                            </div>
                          )}

                          {/* 操作按钮 */}
                          {file.status === "completed" && (
                            <div className="flex gap-2 mt-3">
                              <Button variant="outline" size="sm">
                                <Eye className="w-4 h-4 mr-2" />
                                查看预览
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleReupload(file)}
                              >
                                <RefreshCw className="w-4 h-4 mr-2" />
                                重新上传
                              </Button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 数据预览 */}
          {uploadedFiles.some(f => f.status === "completed" && f.preview_data) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">数据预览</CardTitle>
                <CardDescription>
                  上传文件的预览数据，请确认格式是否正确
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="preview">
                  <TabsList>
                    <TabsTrigger value="preview">数据预览</TabsTrigger>
                    <TabsTrigger value="validation">验证结果</TabsTrigger>
                  </TabsList>

                  <TabsContent value="preview" className="mt-4">
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse border border-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-200 p-2 text-left">账户ID</th>
                            <th className="border border-gray-200 p-2 text-left">账户名称</th>
                            <th className="border border-gray-200 p-2 text-left">平台消耗</th>
                            <th className="border border-gray-200 p-2 text-left">货币</th>
                            <th className="border border-gray-200 p-2 text-left">日期</th>
                          </tr>
                        </thead>
                        <tbody>
                          {uploadedFiles
                            .filter(f => f.preview_data)
                            .flatMap(f => f.preview_data || [])
                            .slice(0, 5)
                            .map((row, index) => (
                              <tr key={index}>
                                <td className="border border-gray-200 p-2">{row.account_id}</td>
                                <td className="border border-gray-200 p-2">{row.account_name}</td>
                                <td className="border border-gray-200 p-2">¥{row.platform_spend.toLocaleString()}</td>
                                <td className="border border-gray-200 p-2">{row.currency}</td>
                                <td className="border border-gray-200 p-2">{row.date}</td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </TabsContent>

                  <TabsContent value="validation" className="mt-4">
                    <div className="space-y-4">
                      {uploadedFiles.map((file) => (
                        file.status === "completed" && (
                          <div key={file.id} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">{file.original_name}</span>
                              <Badge variant={file.invalid_records === 0 ? "default" : "destructive"}>
                                {file.invalid_records === 0 ? "验证通过" : "需要处理"}
                              </Badge>
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-sm">
                              <div>
                                <span className="text-gray-600">总记录数:</span>
                                <span className="ml-2 font-medium">{file.records_count}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">有效记录:</span>
                                <span className="ml-2 font-medium text-green-600">{file.valid_records}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">无效记录:</span>
                                <span className="ml-2 font-medium text-red-600">{file.invalid_records}</span>
                              </div>
                            </div>
                          </div>
                        )
                      ))}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            关闭
          </Button>
          <Button
            onClick={handleClose}
            disabled={!uploadedFiles.some(f => f.status === "completed")}
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            确认上传
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}