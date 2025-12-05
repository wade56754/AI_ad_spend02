/**
 * FinanceTopupTable - 充值申请管理表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React, { useState } from 'react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Search,
  Filter,
  Clock,
  CheckCircle,
  XCircle,
  Eye,
  CreditCard,
  MoreHorizontal,
} from 'lucide-react';
import type { TopupRequest, TopupStatus } from '../types';

interface FinanceTopupTableProps {
  requests: TopupRequest[];
  searchTerm: string;
  statusFilter: TopupStatus | 'all';
  onSearchChange: (value: string) => void;
  onStatusChange: (value: TopupStatus | 'all') => void;
  onApprove: (requestId: number, comment: string) => void;
  onReject: (requestId: number, comment: string) => void;
  onComplete: (requestId: number) => void;
}

const getStatusColor = (status: TopupStatus) => {
  const colors: Record<TopupStatus, string> = {
    pending: 'bg-warning/10 text-warning border-warning/30',
    approved: 'bg-accent/10 text-accent border-accent/30',
    rejected: 'bg-danger/10 text-danger border-danger/30',
    completed: 'bg-success/10 text-success border-success/30',
  };
  return colors[status];
};

const getStatusText = (status: TopupStatus) => {
  const texts: Record<TopupStatus, string> = {
    pending: '待审核',
    approved: '已批准',
    rejected: '已拒绝',
    completed: '已完成',
  };
  return texts[status];
};

const getStatusIcon = (status: TopupStatus) => {
  const icons: Record<TopupStatus, React.ReactNode> = {
    pending: <Clock className="w-3 h-3" />,
    approved: <CheckCircle className="w-3 h-3" />,
    rejected: <XCircle className="w-3 h-3" />,
    completed: <CheckCircle className="w-3 h-3" />,
  };
  return icons[status];
};

export function FinanceTopupTable({
  requests,
  searchTerm,
  statusFilter,
  onSearchChange,
  onStatusChange,
  onApprove,
  onReject,
  onComplete,
}: FinanceTopupTableProps) {
  const [selectedRequest, setSelectedRequest] = useState<TopupRequest | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [showRejectionDialog, setShowRejectionDialog] = useState(false);
  const [reviewComment, setReviewComment] = useState('');

  const handleApprove = (request: TopupRequest) => {
    setSelectedRequest(request);
    setShowApprovalDialog(true);
  };

  const handleReject = (request: TopupRequest) => {
    setSelectedRequest(request);
    setShowRejectionDialog(true);
  };

  const confirmApprove = () => {
    if (selectedRequest) {
      onApprove(selectedRequest.id, '批准充值申请');
    }
    setShowApprovalDialog(false);
    setSelectedRequest(null);
  };

  const confirmReject = () => {
    if (selectedRequest) {
      onReject(selectedRequest.id, reviewComment);
    }
    setShowRejectionDialog(false);
    setSelectedRequest(null);
    setReviewComment('');
  };

  return (
    <div className="space-y-4">
      {/* 筛选和搜索 */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-text-strong">充值申请管理</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted w-4 h-4" />
                <Input
                  placeholder="搜索申请人、账户名或申请理由..."
                  value={searchTerm}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="pl-10 bg-card border-border text-text-body"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select
                value={statusFilter}
                onValueChange={(v) => onStatusChange(v as TopupStatus | 'all')}
              >
                <SelectTrigger className="w-32 bg-card border-border">
                  <SelectValue placeholder="状态筛选" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="pending">待审核</SelectItem>
                  <SelectItem value="approved">已批准</SelectItem>
                  <SelectItem value="rejected">已拒绝</SelectItem>
                  <SelectItem value="completed">已完成</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" className="bg-card border-border">
                <Filter className="w-4 h-4 mr-2" />
                更多筛选
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 申请列表 */}
      <Card className="bg-card border-border">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-border">
                <TableHead className="text-text-muted">申请人</TableHead>
                <TableHead className="text-text-muted">账户信息</TableHead>
                <TableHead className="text-text-muted">申请金额</TableHead>
                <TableHead className="text-text-muted">申请理由</TableHead>
                <TableHead className="text-text-muted">状态</TableHead>
                <TableHead className="text-text-muted">申请时间</TableHead>
                <TableHead className="text-text-muted">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.map((request) => (
                <TableRow key={request.id} className="border-border">
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-accent/10 text-accent">
                          {request.user_name[0]}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-medium text-text-strong">
                          {request.user_name}
                        </div>
                        <div className="text-sm text-text-muted">
                          {request.user_role}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium text-text-body">
                        {request.account_name}
                      </div>
                      <div className="text-sm text-text-muted capitalize">
                        {request.platform}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-semibold text-text-strong">
                      ¥{request.amount.toLocaleString()}
                    </div>
                    <div className="text-sm text-text-muted">{request.currency}</div>
                  </TableCell>
                  <TableCell>
                    <div
                      className="max-w-xs truncate text-text-body"
                      title={request.reason}
                    >
                      {request.reason}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={`flex items-center gap-1 w-fit ${getStatusColor(request.status)}`}
                    >
                      {getStatusIcon(request.status)}
                      {getStatusText(request.status)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm text-text-body">
                      {format(new Date(request.created_at), 'MM/dd HH:mm', {
                        locale: zhCN,
                      })}
                    </div>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>操作</DropdownMenuLabel>
                        <DropdownMenuItem>
                          <Eye className="w-4 h-4 mr-2" />
                          查看详情
                        </DropdownMenuItem>
                        {request.status === 'pending' && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleApprove(request)}>
                              <CheckCircle className="w-4 h-4 mr-2" />
                              批准申请
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleReject(request)}>
                              <XCircle className="w-4 h-4 mr-2" />
                              拒绝申请
                            </DropdownMenuItem>
                          </>
                        )}
                        {request.status === 'approved' && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => onComplete(request.id)}
                            >
                              <CreditCard className="w-4 h-4 mr-2" />
                              标记为完成
                            </DropdownMenuItem>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 批准申请对话框 */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-text-strong">批准充值申请</DialogTitle>
            <DialogDescription className="text-text-muted">
              确认批准此充值申请？批准后财务人员将进行充值操作。
            </DialogDescription>
          </DialogHeader>
          {selectedRequest && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-text-muted">申请人</Label>
                  <div className="font-medium text-text-strong">
                    {selectedRequest.user_name}
                  </div>
                </div>
                <div>
                  <Label className="text-text-muted">账户</Label>
                  <div className="font-medium text-text-strong">
                    {selectedRequest.account_name}
                  </div>
                </div>
                <div>
                  <Label className="text-text-muted">申请金额</Label>
                  <div className="font-semibold text-lg text-text-strong">
                    ¥{selectedRequest.amount.toLocaleString()}
                  </div>
                </div>
                <div>
                  <Label className="text-text-muted">申请时间</Label>
                  <div className="font-medium text-text-strong">
                    {format(new Date(selectedRequest.created_at), 'yyyy-MM-dd HH:mm')}
                  </div>
                </div>
              </div>
              <div>
                <Label className="text-text-muted">申请理由</Label>
                <div className="text-sm text-text-body mt-1">
                  {selectedRequest.reason}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowApprovalDialog(false)}
              className="bg-card border-border"
            >
              取消
            </Button>
            <Button onClick={confirmApprove} className="bg-accent hover:bg-accent/90">
              确认批准
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 拒绝申请对话框 */}
      <Dialog open={showRejectionDialog} onOpenChange={setShowRejectionDialog}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-text-strong">拒绝充值申请</DialogTitle>
            <DialogDescription className="text-text-muted">
              请输入拒绝此申请的原因。原因将通知给申请人。
            </DialogDescription>
          </DialogHeader>
          {selectedRequest && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-text-muted">申请人</Label>
                  <div className="font-medium text-text-strong">
                    {selectedRequest.user_name}
                  </div>
                </div>
                <div>
                  <Label className="text-text-muted">申请金额</Label>
                  <div className="font-semibold text-lg text-text-strong">
                    ¥{selectedRequest.amount.toLocaleString()}
                  </div>
                </div>
              </div>
              <div>
                <Label htmlFor="rejection-reason" className="text-text-muted">
                  拒绝原因 *
                </Label>
                <textarea
                  id="rejection-reason"
                  className="w-full mt-1 p-3 border border-border rounded-md resize-none bg-card text-text-body"
                  rows={3}
                  placeholder="请输入拒绝原因..."
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRejectionDialog(false)}
              className="bg-card border-border"
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={confirmReject}
              disabled={!reviewComment.trim()}
            >
              确认拒绝
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
