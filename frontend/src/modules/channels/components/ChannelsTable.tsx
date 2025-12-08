/**
 * Channels Table Component
 *
 * Displays paginated list of channels with status actions
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

'use client';

import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Edit, Power, PowerOff } from 'lucide-react';
import { useChannels, useActivateChannel, useDeactivateChannel } from '../hooks';
import type { Channel, ChannelListParams } from '../types';

interface ChannelsTableProps {
  onEdit?: (channel: Channel) => void;
}

export function ChannelsTable({ onEdit }: ChannelsTableProps) {
  const [params, setParams] = useState<ChannelListParams>({
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error } = useChannels(params);
  const activateMutation = useActivateChannel();
  const deactivateMutation = useDeactivateChannel();

  const handleActivate = (id: string) => {
    activateMutation.mutate(id);
  };

  const handleDeactivate = (id: string) => {
    deactivateMutation.mutate(id);
  };

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">加载中...</div>;
  }

  if (error) {
    return (
      <div className="py-8 text-center text-destructive">
        加载失败: {error.message}
      </div>
    );
  }

  const channels = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>渠道名称</TableHead>
            <TableHead>渠道代码</TableHead>
            <TableHead>服务费类型</TableHead>
            <TableHead>服务费</TableHead>
            <TableHead>状态</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {channels.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            channels.map((channel) => (
              <TableRow key={channel.id}>
                <TableCell className="font-medium">{channel.name}</TableCell>
                <TableCell>{channel.channel_code || '-'}</TableCell>
                <TableCell>
                  {channel.service_fee_type === 'percent' ? '百分比' : '固定金额'}
                </TableCell>
                <TableCell>
                  {channel.service_fee_type === 'percent'
                    ? `${channel.service_fee_value}%`
                    : `¥${channel.service_fee_value}`}
                </TableCell>
                <TableCell>
                  <Badge variant={channel.is_active ? 'default' : 'secondary'}>
                    {channel.is_active ? '启用' : '停用'}
                  </Badge>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onEdit?.(channel)}>
                        <Edit className="mr-2 h-4 w-4" />
                        编辑
                      </DropdownMenuItem>
                      {channel.is_active ? (
                        <DropdownMenuItem
                          onClick={() => handleDeactivate(channel.id)}
                          disabled={deactivateMutation.isPending}
                        >
                          <PowerOff className="mr-2 h-4 w-4" />
                          停用
                        </DropdownMenuItem>
                      ) : (
                        <DropdownMenuItem
                          onClick={() => handleActivate(channel.id)}
                          disabled={activateMutation.isPending}
                        >
                          <Power className="mr-2 h-4 w-4" />
                          启用
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            共 {pagination.total} 条，第 {pagination.page} / {pagination.total_pages} 页
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.total_pages}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
