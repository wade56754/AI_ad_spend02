"use client";

import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  CalendarIcon,
  Plus,
  X,
  Users,
  Target,
  DollarSign,
  FileText,
  AlertTriangle,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

// 类型定义
interface User {
  id: number;
  username: string;
  nickname: string;
  role: string;
  status: string;
}

interface Client {
  id: number;
  name: string;
  contact_person: string;
  email: string;
  status: string;
}

interface ProjectFormData {
  name: string;
  client_id?: number;
  client_name?: string;
  description: string;
  currency: string;
  budget: number;
  priority: "low" | "medium" | "high";
  status: "planning" | "active" | "paused" | "completed" | "archived";
  start_date: Date;
  end_date: Date;
  team_lead_id?: number;
  team_members: number[];
  tags: string[];
  objectives: string[];
  deliverables: string[];
  notes: string;
}

interface ProjectFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: any) => Promise<void>;
  editData?: ProjectFormData | null;
  mode: "create" | "edit";
}

export function ProjectForm({
  open,
  onClose,
  onSubmit,
  editData,
  mode,
}: ProjectFormProps) {
  const [formData, setFormData] = useState<ProjectFormData>({
    name: "",
    description: "",
    currency: "USD",
    budget: 0,
    priority: "medium",
    status: "planning",
    start_date: new Date(),
    end_date: new Date(new Date().setMonth(new Date().getMonth() + 3)),
    team_members: [],
    tags: [],
    objectives: [],
    deliverables: [],
    notes: "",
  });

  const [users, setUsers] = useState<User[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);
  const [newTag, setNewTag] = useState("");
  const [newObjective, setNewObjective] = useState("");
  const [newDeliverable, setNewDeliverable] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      const response = await fetch("/api/v1/users?status=active");
      const result = await response.json();
      if (result.success) {
        setUsers(result.data);
      }
    } catch (error) {
      console.error("获取用户列表失败:", error);
    }
  };

  // 获取客户列表
  const fetchClients = async () => {
    try {
      const response = await fetch("/api/v1/clients?status=active");
      const result = await response.json();
      if (result.success) {
        setClients(result.data);
      }
    } catch (error) {
      console.error("获取客户列表失败:", error);
    }
  };

  // 表单验证
  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "项目名称不能为空";
    }

    if (!formData.description.trim()) {
      newErrors.description = "项目描述不能为空";
    }

    if (!formData.budget || formData.budget <= 0) {
      newErrors.budget = "预算必须大于0";
    }

    if (formData.start_date >= formData.end_date) {
      newErrors.end_date = "结束日期必须晚于开始日期";
    }

    if (formData.objectives.length === 0) {
      newErrors.objectives = "至少需要添加一个项目目标";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const submitData = {
        ...formData,
        start_date: format(formData.start_date, "yyyy-MM-dd"),
        end_date: format(formData.end_date, "yyyy-MM-dd"),
      };

      await onSubmit(submitData);
    } catch (error) {
      console.error("提交失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 添加标签
  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, newTag.trim()],
      });
      setNewTag("");
    }
  };

  // 删除标签
  const handleRemoveTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove),
    });
  };

  // 添加目标
  const handleAddObjective = () => {
    if (newObjective.trim()) {
      setFormData({
        ...formData,
        objectives: [...formData.objectives, newObjective.trim()],
      });
      setNewObjective("");
    }
  };

  // 删除目标
  const handleRemoveObjective = (index: number) => {
    setFormData({
      ...formData,
      objectives: formData.objectives.filter((_, i) => i !== index),
    });
  };

  // 添加交付物
  const handleAddDeliverable = () => {
    if (newDeliverable.trim()) {
      setFormData({
        ...formData,
        deliverables: [...formData.deliverables, newDeliverable.trim()],
      });
      setNewDeliverable("");
    }
  };

  // 删除交付物
  const handleRemoveDeliverable = (index: number) => {
    setFormData({
      ...formData,
      deliverables: formData.deliverables.filter((_, i) => i !== index),
    });
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      currency: "USD",
      budget: 0,
      priority: "medium",
      status: "planning",
      start_date: new Date(),
      end_date: new Date(new Date().setMonth(new Date().getMonth() + 3)),
      team_members: [],
      tags: [],
      objectives: [],
      deliverables: [],
      notes: "",
    });
    setErrors({});
    setNewTag("");
    setNewObjective("");
    setNewDeliverable("");
  };

  // 初始化编辑数据
  useEffect(() => {
    if (editData) {
      setFormData({
        ...editData,
        start_date: new Date(editData.start_date),
        end_date: new Date(editData.end_date),
      });
    } else {
      resetForm();
    }
  }, [editData, open]);

  useEffect(() => {
    if (open) {
      fetchUsers();
      fetchClients();
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            {mode === "create" ? "创建新项目" : "编辑项目"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create" ? "创建一个新的广告投放项目" : "编辑项目信息"}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">基本信息</CardTitle>
              <CardDescription>项目的基本配置信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">
                    项目名称 <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="输入项目名称"
                    className={errors.name ? "border-red-500" : ""}
                  />
                  {errors.name && (
                    <p className="text-sm text-red-500 mt-1">{errors.name}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="client">客户</Label>
                  <Select
                    value={formData.client_id?.toString()}
                    onValueChange={(value) => {
                      const clientId = value ? parseInt(value) : undefined;
                      const client = clients.find(c => c.id === clientId);
                      setFormData({
                        ...formData,
                        client_id: clientId,
                        client_name: client?.name,
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择客户" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">无关联客户</SelectItem>
                      {clients.map((client) => (
                        <SelectItem key={client.id} value={client.id.toString()}>
                          {client.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="description">
                  项目描述 <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="详细描述项目的目标、范围和要求"
                  rows={3}
                  className={errors.description ? "border-red-500" : ""}
                />
                {errors.description && (
                  <p className="text-sm text-red-500 mt-1">{errors.description}</p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="currency">币种</Label>
                  <Select
                    value={formData.currency}
                    onValueChange={(value) => setFormData({ ...formData, currency: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="USD">USD - 美元</SelectItem>
                      <SelectItem value="EUR">EUR - 欧元</SelectItem>
                      <SelectItem value="GBP">GBP - 英镑</SelectItem>
                      <SelectItem value="CNY">CNY - 人民币</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="budget">
                    项目预算 <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="budget"
                    type="number"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: parseFloat(e.target.value) || 0 })}
                    placeholder="输入项目预算"
                    className={errors.budget ? "border-red-500" : ""}
                  />
                  {errors.budget && (
                    <p className="text-sm text-red-500 mt-1">{errors.budget}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="priority">优先级</Label>
                  <Select
                    value={formData.priority}
                    onValueChange={(value: any) => setFormData({ ...formData, priority: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">低</SelectItem>
                      <SelectItem value="medium">中</SelectItem>
                      <SelectItem value="high">高</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="status">项目状态</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value: any) => setFormData({ ...formData, status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="planning">规划中</SelectItem>
                      <SelectItem value="active">进行中</SelectItem>
                      <SelectItem value="paused">暂停</SelectItem>
                      <SelectItem value="completed">已完成</SelectItem>
                      <SelectItem value="archived">已归档</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="team_lead">项目负责人</Label>
                  <Select
                    value={formData.team_lead_id?.toString()}
                    onValueChange={(value) => setFormData({
                      ...formData,
                      team_lead_id: value ? parseInt(value) : undefined
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择项目负责人" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">未指定</SelectItem>
                      {users
                        .filter(user => user.status === "active")
                        .map((user) => (
                        <SelectItem key={user.id} value={user.id.toString()}>
                          {user.nickname} ({user.username})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>开始日期</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !formData.start_date && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {formData.start_date ? format(formData.start_date, "yyyy年MM月dd日") : "选择日期"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={formData.start_date}
                        onSelect={(date) => date && setFormData({ ...formData, start_date: date })}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                <div>
                  <Label>结束日期</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !formData.end_date && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {formData.end_date ? format(formData.end_date, "yyyy年MM月dd日") : "选择日期"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={formData.end_date}
                        onSelect={(date) => date && setFormData({ ...formData, end_date: date })}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                  {errors.end_date && (
                    <p className="text-sm text-red-500 mt-1">{errors.end_date}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 项目标签 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">项目标签</CardTitle>
              <CardDescription>添加标签便于分类和搜索</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="输入标签名称"
                    onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
                  />
                  <Button type="button" onClick={handleAddTag}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-red-600"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 项目目标 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">项目目标</CardTitle>
              <CardDescription>定义项目的主要目标和成功指标</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {errors.objectives && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>{errors.objectives}</AlertDescription>
                  </Alert>
                )}
                <div className="flex gap-2">
                  <Input
                    value={newObjective}
                    onChange={(e) => setNewObjective(e.target.value)}
                    placeholder="输入项目目标"
                    onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), handleAddObjective())}
                  />
                  <Button type="button" onClick={handleAddObjective}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-2">
                  {formData.objectives.map((objective, index) => (
                    <div key={index} className="flex items-center gap-2 p-3 border rounded-lg">
                      <Target className="w-4 h-4 text-blue-500" />
                      <span className="flex-1">{objective}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveObjective(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 交付物 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">主要交付物</CardTitle>
              <CardDescription>列出项目需要交付的主要成果</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    value={newDeliverable}
                    onChange={(e) => setNewDeliverable(e.target.value)}
                    placeholder="输入交付物描述"
                    onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), handleAddDeliverable())}
                  />
                  <Button type="button" onClick={handleAddDeliverable}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-2">
                  {formData.deliverables.map((deliverable, index) => (
                    <div key={index} className="flex items-center gap-2 p-3 border rounded-lg">
                      <FileText className="w-4 h-4 text-green-500" />
                      <span className="flex-1">{deliverable}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveDeliverable(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 备注 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">备注说明</CardTitle>
              <CardDescription>其他需要说明的信息</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="输入项目相关的备注信息..."
                rows={3}
              />
            </CardContent>
          </Card>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              取消
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "保存中..." : (mode === "create" ? "创建项目" : "保存修改")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}