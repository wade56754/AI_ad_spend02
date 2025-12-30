/**
 * Project Members Dialog Component
 *
 * Dialog for managing project team members
 * SoT: DATA_SCHEMA.md v5.2 (project_members entity)
 */

'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Users,
  UserPlus,
  Trash2,
  Loader2,
  Search,
} from 'lucide-react';
import { toast } from 'sonner';
import { useProjectMembers, useAssignMember, useRemoveMember } from '../hooks';
import type { Project, ProjectMember, ProjectMemberAssignInput } from '../types';
import { PROJECT_ROLE_CONFIG } from '../types';

interface ProjectMembersDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project: Project;
}

export function ProjectMembersDialog({
  open,
  onOpenChange,
  project,
}: ProjectMembersDialogProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState<ProjectMember | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  // SoT: MASTER.md v4.6 §2.4 - 默认角色为投手 (pitcher)
  const [newMember, setNewMember] = useState<ProjectMemberAssignInput>({
    user_id: '',
    role: 'pitcher',
  });

  // Fetch project members
  const { data: membersData, isLoading: isLoadingMembers } = useProjectMembers(project.id, {
    enabled: open,
  });

  const members = membersData?.data ?? [];

  // Mutations
  const assignMember = useAssignMember({
    onSuccess: () => {
      toast.success('成员添加成功');
      setShowAddForm(false);
      setNewMember({ user_id: '', role: 'pitcher' });
    },
    onError: (error) => {
      toast.error(error.message || '添加成员失败');
    },
  });

  const removeMember = useRemoveMember({
    onSuccess: () => {
      toast.success('成员移除成功');
      setMemberToRemove(null);
    },
    onError: (error) => {
      toast.error(error.message || '移除成员失败');
    },
  });

  // Filter members by search
  const filteredMembers = members.filter(
    (member) =>
      member.user_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.user_email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Handle add member
  const handleAddMember = () => {
    if (!newMember.user_id) {
      toast.error('请输入用户 ID');
      return;
    }

    assignMember.mutate({
      projectId: project.id,
      input: newMember,
    });
  };

  // Handle remove member
  const handleRemoveMember = () => {
    if (!memberToRemove) return;

    removeMember.mutate({
      projectId: project.id,
      userId: memberToRemove.user_id,
    });
  };

  // Get initials for avatar
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Get role badge color - SoT: MASTER.md v4.6 §2.4
  const getRoleBadgeVariant = (role: string): 'default' | 'secondary' | 'outline' => {
    switch (role) {
      case 'account_manager':
        return 'default';
      case 'pitcher':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[700px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              项目成员管理
            </DialogTitle>
            <DialogDescription>
              管理「{project.name}」项目的团队成员
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Search and Add */}
            <div className="flex items-center justify-between gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜索成员..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Button
                size="sm"
                onClick={() => setShowAddForm(!showAddForm)}
              >
                <UserPlus className="h-4 w-4 mr-2" />
                添加成员
              </Button>
            </div>

            {/* Add Member Form */}
            {showAddForm && (
              <div className="rounded-lg border bg-gray-50 p-4 space-y-4">
                <h4 className="font-medium text-sm">添加新成员</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="user_id">用户 ID *</Label>
                    <Input
                      id="user_id"
                      placeholder="输入用户 ID"
                      value={newMember.user_id as string}
                      onChange={(e) =>
                        setNewMember((prev) => ({ ...prev, user_id: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">项目角色 *</Label>
                    <Select
                      value={newMember.role}
                      onValueChange={(value: 'account_manager' | 'pitcher' | 'analyst') =>
                        setNewMember((prev) => ({ ...prev, role: value }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(PROJECT_ROLE_CONFIG).map(([role, config]) => (
                          <SelectItem key={role} value={role}>
                            {config.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddForm(false)}
                    disabled={assignMember.isPending}
                  >
                    取消
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleAddMember}
                    disabled={assignMember.isPending}
                  >
                    {assignMember.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        添加中...
                      </>
                    ) : (
                      '确认添加'
                    )}
                  </Button>
                </div>
              </div>
            )}

            {/* Members Table */}
            <div className="rounded-lg border">
              {isLoadingMembers ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : filteredMembers.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  {searchQuery ? '未找到匹配的成员' : '暂无项目成员'}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>成员</TableHead>
                      <TableHead>系统角色</TableHead>
                      <TableHead>项目角色</TableHead>
                      <TableHead>加入时间</TableHead>
                      <TableHead className="w-[60px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredMembers.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar className="h-8 w-8">
                              <AvatarFallback className="text-xs">
                                {getInitials(member.user_name)}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="font-medium">{member.user_name}</p>
                              <p className="text-xs text-muted-foreground">
                                {member.user_email}
                              </p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{member.user_role}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getRoleBadgeVariant(member.project_role)}>
                            {PROJECT_ROLE_CONFIG[member.project_role]?.label || member.project_role}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {new Date(member.joined_at).toLocaleDateString('zh-CN')}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                            onClick={() => setMemberToRemove(member)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>

            {/* Members Count */}
            <div className="text-sm text-muted-foreground">
              共 {members.length} 名成员
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove Confirmation Dialog */}
      <AlertDialog
        open={!!memberToRemove}
        onOpenChange={(open) => !open && setMemberToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认移除成员</AlertDialogTitle>
            <AlertDialogDescription>
              确定要将「{memberToRemove?.user_name}」从项目「{project.name}」中移除吗？
              此操作不可撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={removeMember.isPending}>
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRemoveMember}
              disabled={removeMember.isPending}
              className="bg-red-600 hover:bg-red-700"
            >
              {removeMember.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  移除中...
                </>
              ) : (
                '确认移除'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default ProjectMembersDialog;
