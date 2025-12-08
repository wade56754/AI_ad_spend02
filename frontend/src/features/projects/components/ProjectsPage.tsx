/**
 * Projects Page Component
 *
 * Main page for project management
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { ProjectsTable } from './ProjectsTable';
import { ProjectForm } from './ProjectForm';
import type { Project } from '../types';

export function ProjectsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  const handleCreate = () => {
    setEditingProject(null);
    setFormOpen(true);
  };

  const handleEdit = (project: Project) => {
    setEditingProject(project);
    setFormOpen(true);
  };

  const handleFormClose = (open: boolean) => {
    setFormOpen(open);
    if (!open) {
      setEditingProject(null);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">项目管理</h1>
          <p className="text-muted-foreground">管理广告投放项目及预算</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          新建项目
        </Button>
      </div>

      <ProjectsTable onEdit={handleEdit} />

      <ProjectForm
        project={editingProject}
        open={formOpen}
        onOpenChange={handleFormClose}
      />
    </div>
  );
}
