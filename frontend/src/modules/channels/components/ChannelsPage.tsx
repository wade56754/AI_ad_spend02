/**
 * Channels Page Component
 *
 * Main page for channel management
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { ChannelsTable } from './ChannelsTable';
import { ChannelForm } from './ChannelForm';
import type { Channel } from '../types';

export function ChannelsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingChannel, setEditingChannel] = useState<Channel | null>(null);

  const handleCreate = () => {
    setEditingChannel(null);
    setFormOpen(true);
  };

  const handleEdit = (channel: Channel) => {
    setEditingChannel(channel);
    setFormOpen(true);
  };

  const handleFormClose = (open: boolean) => {
    setFormOpen(open);
    if (!open) {
      setEditingChannel(null);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">渠道管理</h1>
          <p className="text-muted-foreground">管理广告投放渠道及服务费配置</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          新建渠道
        </Button>
      </div>

      <ChannelsTable onEdit={handleEdit} />

      <ChannelForm
        channel={editingChannel}
        open={formOpen}
        onOpenChange={handleFormClose}
      />
    </div>
  );
}
