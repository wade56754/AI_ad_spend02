/**
 * Import Jobs Page Component
 *
 * Main page for import job management
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Upload } from 'lucide-react';
import { ImportJobsTable } from './ImportJobsTable';
import { ImportJobUpload } from './ImportJobUpload';

export function ImportJobsPage() {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">导入任务</h1>
          <p className="text-muted-foreground">管理数据导入任务</p>
        </div>
        <Button onClick={() => setUploadOpen(true)}>
          <Upload className="mr-2 h-4 w-4" />
          上传文件
        </Button>
      </div>

      <ImportJobsTable />
      <ImportJobUpload open={uploadOpen} onOpenChange={setUploadOpen} />
    </div>
  );
}
