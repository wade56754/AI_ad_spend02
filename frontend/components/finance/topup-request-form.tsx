"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle,
  CreditCard,
  Calculator,
  TrendingUp,
  DollarSign,
  Info,
  HelpCircle,
  Eye,
  Download,
  X
} from "lucide-react";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

// 类型定义
interface AdAccount {
  id: number;
  account_name: string;
  platform: string;
  account_id: string;
  current_balance: number;
  currency: string;
  spending_limit: number;
  assigned_user_name: string;
  status: string;
}

interface Project {
  id: number;
  name: string;
  client_name: string;
  budget: number;
  current_spend: number;
  currency: string;
  end_date: string;
}

interface TopupRequestFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (request: any) => void;
  initialData?: any;
}

export function TopupRequestForm({ isOpen, onClose, onSubmit, initialData }: TopupRequestFormProps) {
  const [activeTab, setActiveTab] = useState("basic");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewAmount, setPreviewAmount] = useState(0);

  // 表单状态
  const [formData, setFormData] = useState({
    account_id: "",
    project_id: "",
    amount: "",
    currency: "CNY",
    urgency_level: "normal",
    reason: "",
    expected_impact: "",
    alternative_plans: "",
    supporting_documents: [] as File[],
    request_type: "regular",
    scheduled_date: "",
  });

  // 模拟数据
  const [adAccounts] = useState<AdAccount[]>([
    {
      id: 1,
      account_name: "Facebook广告账户01",
      platform: "facebook",
      account_id: "act_1234567890",
      current_balance: 5000,
      currency: "CNY",
      spending_limit: 100000,
      assigned_user_name: "张三",
      status: "active"
    },
    {
      id: 2,
      account_name: "TikTok广告账户02",
      platform: "tiktok",
      account_id: "adv_0987654321",
      current_balance: 2000,
      currency: "CNY",
      spending_limit: 80000,
      assigned_user_name: "李四",
      status: "active"
    },
    {
      id: 3,
      account_name: "Google Ads账户03",
      platform: "google",
      account_id: "123-456-7890",
      current_balance: 8000,
      currency: "CNY",
      spending_limit: 120000,
      assigned_user_name: "王五",
      status: "active"
    },
  ]);

  const [projects] = useState<Project[]>([
    {
      id: 1,
      name: "美妆品牌推广项目",
      client_name: "雅诗兰黛",
      budget: 200000,
      current_spend: 85000,
      currency: "CNY",
      end_date: "2025-02-28"
    },
    {
      id: 2,
      name: "电商大促活动",
      client_name: "京东商城",
      budget: 500000,
      current_spend: 320000,
      currency: "CNY",
      end_date: "2025-01-31"
    },
    {
      id: 3,
      name: "游戏发行推广",
      client_name: "腾讯游戏",
      budget: 150000,
      current_spend: 45000,
      currency: "CNY",
      end_date: "2025-03-15"
    },
  ]);

  const urgencyLevels = [
    { value: "low", label: "普通", color: "bg-green-100 text-green-700", description: "3-5个工作日处理" },
    { value: "normal", label: "标准", color: "bg-blue-100 text-blue-700", description: "1-2个工作日处理" },
    { value: "high", label: "紧急", color: "bg-yellow-100 text-yellow-700", description: "24小时内处理" },
    { value: "urgent", label: "特急", color: "bg-red-100 text-red-700", description: "需要立即处理" },
  ];

  const requestTypes = [
    { value: "regular", label: "常规充值", description: "日常运营资金补充" },
    { value: "campaign", label: "活动充值", description: "特定推广活动资金需求" },
    { value: "emergency", label: "紧急充值", description: "账户余额不足紧急补充" },
    { value: "strategic", label: "战略充值", description: "重要项目战略资金储备" },
  ];

  // 获取平台图标
  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case "facebook": return "📘";
      case "tiktok": return "🎵";
      case "google": return "🔍";
      case "twitter": return "🐦";
      default: return "📱";
    }
  };

  // 获取余额状态颜色
  const getBalanceStatusColor = (balance: number, limit: number) => {
    const percentage = (balance / limit) * 100;
    if (percentage < 10) return "text-red-600";
    if (percentage < 25) return "text-yellow-600";
    return "text-green-600";
  };

  // 处理表单字段变化
  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // 计算预览金额
    if (field === "amount") {
      setPreviewAmount(Number(value) || 0);
    }
  };

  // 处理文件上传
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const newFiles = Array.from(files);
      setFormData(prev => ({
        ...prev,
        supporting_documents: [...prev.supporting_documents, ...newFiles]
      }));
    }
  };

  // 移除上传的文件
  const removeFile = (index: number) => {
    setFormData(prev => ({
      ...prev,
      supporting_documents: prev.supporting_documents.filter((_, i) => i !== index)
    }));
  };

  // 获取选中的账户信息
  const selectedAccount = adAccounts.find(account => account.id === Number(formData.account_id));
  const selectedProject = projects.find(project => project.id === Number(formData.project_id));
  const selectedUrgency = urgencyLevels.find(level => level.value === formData.urgency_level);
  const selectedRequestType = requestTypes.find(type => type.value === formData.request_type);

  // 验证表单
  const validateForm = () => {
    if (!formData.account_id) {
      alert("请选择广告账户");
      return false;
    }
    if (!formData.amount || Number(formData.amount) <= 0) {
      alert("请输入有效的充值金额");
      return false;
    }
    if (!formData.reason.trim()) {
      alert("请填写申请理由");
      return false;
    }
    return true;
  };

  // 提交表单
  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const requestData = {
        account_id: Number(formData.account_id),
        project_id: formData.project_id ? Number(formData.project_id) : null,
        amount: Number(formData.amount),
        currency: formData.currency,
        urgency_level: formData.urgency_level,
        reason: formData.reason,
        expected_impact: formData.expected_impact,
        alternative_plans: formData.alternative_plans,
        request_type: formData.request_type,
        scheduled_date: formData.scheduled_date,
        supporting_documents: formData.supporting_documents,
      };

      await onSubmit(requestData);
      onClose();
      // 重置表单
      setFormData({
        account_id: "",
        project_id: "",
        amount: "",
        currency: "CNY",
        urgency_level: "normal",
        reason: "",
        expected_impact: "",
        alternative_plans: "",
        supporting_documents: [],
        request_type: "regular",
        scheduled_date: "",
      });
    } catch (error) {
      console.error("提交失败:", error);
      alert("提交失败，请重试");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            充值申请
          </DialogTitle>
          <DialogDescription>
            提交广告账户充值申请，请详细填写相关信息以便快速审批
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="basic">基本信息</TabsTrigger>
            <TabsTrigger value="detail">详细说明</TabsTrigger>
            <TabsTrigger value="documents">支持文档</TabsTrigger>
            <TabsTrigger value="preview">申请预览</TabsTrigger>
          </TabsList>

          {/* 基本信息 */}
          <TabsContent value="basic" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 广告账户选择 */}
              <div className="space-y-2">
                <Label htmlFor="account_id">广告账户 *</Label>
                <Select value={formData.account_id} onValueChange={(value) => handleInputChange("account_id", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择广告账户" />
                  </SelectTrigger>
                  <SelectContent>
                    {adAccounts.map((account) => (
                      <SelectItem key={account.id} value={account.id.toString()}>
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center gap-2">
                            <span>{getPlatformIcon(account.platform)}</span>
                            <span>{account.account_name}</span>
                          </div>
                          <div className={`text-xs ${getBalanceStatusColor(account.current_balance, account.spending_limit)}`}>
                            ¥{account.current_balance.toLocaleString()}
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedAccount && (
                  <div className="text-sm text-gray-600 p-3 bg-gray-50 rounded-md">
                    <div className="grid grid-cols-2 gap-2">
                      <div>平台: <span className="font-medium capitalize">{selectedAccount.platform}</span></div>
                      <div>账户ID: <span className="font-medium">{selectedAccount.account_id}</span></div>
                      <div>当前余额: <span className={`font-medium ${getBalanceStatusColor(selectedAccount.current_balance, selectedAccount.spending_limit)}`}>¥{selectedAccount.current_balance.toLocaleString()}</span></div>
                      <div>消费限额: <span className="font-medium">¥{selectedAccount.spending_limit.toLocaleString()}</span></div>
                      <div>负责人: <span className="font-medium">{selectedAccount.assigned_user_name}</span></div>
                      <div>状态: <span className="font-medium">{selectedAccount.status === "active" ? "正常" : "异常"}</span></div>
                    </div>
                  </div>
                )}
              </div>

              {/* 关联项目 */}
              <div className="space-y-2">
                <Label htmlFor="project_id">关联项目</Label>
                <Select value={formData.project_id} onValueChange={(value) => handleInputChange("project_id", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择关联项目（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">无关联项目</SelectItem>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={project.id.toString()}>
                        <div className="flex flex-col">
                          <span>{project.name}</span>
                          <span className="text-xs text-gray-500">{project.client_name}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedProject && (
                  <div className="text-sm text-gray-600 p-3 bg-gray-50 rounded-md">
                    <div className="grid grid-cols-2 gap-2">
                      <div>客户: <span className="font-medium">{selectedProject.client_name}</span></div>
                      <div>项目预算: <span className="font-medium">¥{selectedProject.budget.toLocaleString()}</span></div>
                      <div>已消耗: <span className="font-medium">¥{selectedProject.current_spend.toLocaleString()}</span></div>
                      <div>剩余预算: <span className="font-medium">¥{(selectedProject.budget - selectedProject.current_spend).toLocaleString()}</span></div>
                    </div>
                  </div>
                )}
              </div>

              {/* 充值金额 */}
              <div className="space-y-2">
                <Label htmlFor="amount">充值金额 (¥) *</Label>
                <Input
                  id="amount"
                  type="number"
                  placeholder="请输入充值金额"
                  value={formData.amount}
                  onChange={(e) => handleInputChange("amount", e.target.value)}
                  min="0"
                  step="100"
                />
                {selectedAccount && previewAmount > 0 && (
                  <div className="text-sm text-gray-600">
                    充值后余额: <span className="font-medium text-green-600">
                      ¥{(selectedAccount.current_balance + previewAmount).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>

              {/* 申请类型 */}
              <div className="space-y-2">
                <Label htmlFor="request_type">申请类型</Label>
                <Select value={formData.request_type} onValueChange={(value) => handleInputChange("request_type", value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {requestTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex flex-col">
                          <span>{type.label}</span>
                          <span className="text-xs text-gray-500">{type.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedRequestType && (
                  <div className="text-sm text-gray-600">
                    {selectedRequestType.description}
                  </div>
                )}
              </div>

              {/* 紧急程度 */}
              <div className="space-y-2">
                <Label htmlFor="urgency_level">紧急程度</Label>
                <Select value={formData.urgency_level} onValueChange={(value) => handleInputChange("urgency_level", value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {urgencyLevels.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        <div className="flex items-center gap-2">
                          <Badge className={level.color}>
                            {level.label}
                          </Badge>
                          <span className="text-xs text-gray-500">{level.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedUrgency && (
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      {selectedUrgency.description}
                    </AlertDescription>
                  </Alert>
                )}
              </div>

              {/* 计划充值时间 */}
              <div className="space-y-2">
                <Label htmlFor="scheduled_date">计划充值时间</Label>
                <Input
                  id="scheduled_date"
                  type="date"
                  value={formData.scheduled_date}
                  onChange={(e) => handleInputChange("scheduled_date", e.target.value)}
                  min={format(new Date(), "yyyy-MM-dd")}
                />
              </div>
            </div>
          </TabsContent>

          {/* 详细说明 */}
          <TabsContent value="detail" className="space-y-6">
            <div className="space-y-4">
              {/* 申请理由 */}
              <div className="space-y-2">
                <Label htmlFor="reason">申请理由 *</Label>
                <Textarea
                  id="reason"
                  placeholder="请详细说明充值原因，包括具体的业务需求和市场情况..."
                  value={formData.reason}
                  onChange={(e) => handleInputChange("reason", e.target.value)}
                  rows={4}
                  className="resize-none"
                />
                <div className="text-xs text-gray-500">
                  请详细说明充值的具体原因，有助于加快审批速度
                </div>
              </div>

              {/* 预期效果 */}
              <div className="space-y-2">
                <Label htmlFor="expected_impact">预期效果</Label>
                <Textarea
                  id="expected_impact"
                  placeholder="描述本次充值预期带来的业务效果和ROI..."
                  value={formData.expected_impact}
                  onChange={(e) => handleInputChange("expected_impact", e.target.value)}
                  rows={3}
                  className="resize-none"
                />
                <div className="text-xs text-gray-500">
                  说明预期带来的转化量、曝光量或其他关键指标提升
                </div>
              </div>

              {/* 备选方案 */}
              <div className="space-y-2">
                <Label htmlFor="alternative_plans">备选方案</Label>
                <Textarea
                  id="alternative_plans"
                  placeholder="如果申请被拒绝或延迟，有什么备选方案..."
                  value={formData.alternative_plans}
                  onChange={(e) => handleInputChange("alternative_plans", e.target.value)}
                  rows={3}
                  className="resize-none"
                />
                <div className="text-xs text-gray-500">
                  描述如果充值无法及时到位的替代解决方案
                </div>
              </div>

              {/* 历史充值记录 */}
              {selectedAccount && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      该账户历史充值记录
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span>最近一次充值: 2025-01-08</span>
                        <span className="font-medium">¥30,000</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>本月累计充值: ¥80,000</span>
                        <span className="text-green-600">正常</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>平均审批时间: 1.5天</span>
                        <span className="text-blue-600">快速</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* 支持文档 */}
          <TabsContent value="documents" className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label>上传支持文档</Label>
                <div className="mt-2 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="mt-2">
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <span className="text-blue-600 hover:text-blue-500">选择文件</span>
                      <span className="text-gray-500"> 或拖拽文件到此处</span>
                    </label>
                    <input
                      id="file-upload"
                      type="file"
                      className="hidden"
                      multiple
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
                      onChange={handleFileUpload}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    支持 PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, JPEG 格式，单个文件不超过 10MB
                  </p>
                </div>
              </div>

              {/* 已上传文件列表 */}
              {formData.supporting_documents.length > 0 && (
                <div className="space-y-2">
                  <Label>已上传文件</Label>
                  <div className="space-y-2">
                    {formData.supporting_documents.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-gray-400" />
                          <div>
                            <div className="text-sm font-medium">{file.name}</div>
                            <div className="text-xs text-gray-500">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(index)}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 文件类型建议 */}
              <Alert>
                <HelpCircle className="h-4 w-4" />
                <AlertDescription>
                  建议上传项目计划书、广告排期表、ROI预测表等相关文档，有助于提高审批通过率
                </AlertDescription>
              </Alert>
            </div>
          </TabsContent>

          {/* 申请预览 */}
          <TabsContent value="preview" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="w-5 h-5" />
                  申请预览
                </CardTitle>
                <CardDescription>
                  请仔细检查以下信息，确认无误后提交申请
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 基本信息 */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm text-gray-600">广告账户</Label>
                    <div className="font-medium">
                      {selectedAccount ? selectedAccount.account_name : "未选择"}
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">充值金额</Label>
                    <div className="font-medium text-lg text-blue-600">
                      ¥{Number(formData.amount || 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">申请类型</Label>
                    <div className="font-medium">
                      {selectedRequestType ? selectedRequestType.label : "未选择"}
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-600">紧急程度</Label>
                    <div>
                      {selectedUrgency && (
                        <Badge className={selectedUrgency.color}>
                          {selectedUrgency.label}
                        </Badge>
                      )}
                    </div>
                  </div>
                  {selectedProject && (
                    <div>
                      <Label className="text-sm text-gray-600">关联项目</Label>
                      <div className="font-medium">{selectedProject.name}</div>
                    </div>
                  )}
                  {formData.scheduled_date && (
                    <div>
                      <Label className="text-sm text-gray-600">计划充值时间</Label>
                      <div className="font-medium">{formData.scheduled_date}</div>
                    </div>
                  )}
                </div>

                {/* 申请理由 */}
                {formData.reason && (
                  <div>
                    <Label className="text-sm text-gray-600">申请理由</Label>
                    <div className="mt-1 p-3 bg-gray-50 rounded-md text-sm">
                      {formData.reason}
                    </div>
                  </div>
                )}

                {/* 支持文档 */}
                {formData.supporting_documents.length > 0 && (
                  <div>
                    <Label className="text-sm text-gray-600">支持文档</Label>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {formData.supporting_documents.map((file, index) => (
                        <Badge key={index} variant="secondary" className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {file.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* 注意事项 */}
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    提交后申请将进入审批流程，您可以在财务管理页面查看审批进度。
                    紧急申请将在24小时内处理，常规申请将在1-2个工作日内处理。
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            取消
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="min-w-[100px]"
          >
            {isSubmitting ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                提交中...
              </div>
            ) : (
              "提交申请"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}