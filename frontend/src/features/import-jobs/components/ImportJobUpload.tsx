/**
 * Import Job Upload Component
 *
 * File upload dialog for creating new import jobs
 */

'use client';

import { useRef, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, FileSpreadsheet, X } from 'lucide-react';
import { useUploadImportFile } from '../hooks';
import { IMPORT_JOB_TYPE_CONFIG } from '../types';
import type { ImportJobType } from '../types';

interface ImportJobUploadProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ImportJobUpload({ open, onOpenChange }: ImportJobUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobType, setJobType] = useState<ImportJobType>('finance');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useUploadImportFile();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        alert('仅支持 CSV 格式文件');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        alert('仅支持 CSV 格式文件');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const clearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      await uploadMutation.mutateAsync({ file: selectedFile, jobType });
      setSelectedFile(null);
      setJobType('finance');
      onOpenChange(false);
    } catch (error) {
      console.error('上传失败:', error);
    }
  };

  const handleClose = () => {
    if (!uploadMutation.isPending) {
      clearFile();
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>上传导入文件</DialogTitle>
          <DialogDescription>
            选择 CSV 格式文件进行数据导入
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>导入类型</Label>
            <Select value={jobType} onValueChange={(v) => setJobType(v as ImportJobType)}>
              <SelectTrigger>
                <SelectValue placeholder="选择导入类型" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(IMPORT_JOB_TYPE_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>文件选择</Label>
            <div
              className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              {selectedFile ? (
                <div className="flex items-center justify-center gap-2">
                  <FileSpreadsheet className="h-8 w-8 text-green-600" />
                  <div className="text-left">
                    <p className="font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="ml-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearFile();
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                  <p className="text-muted-foreground">
                    点击或拖拽文件到此处上传
                  </p>
                  <p className="text-xs text-muted-foreground">
                    仅支持 CSV 格式
                  </p>
                </div>
              )}
            </div>
            <Input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileSelect}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={uploadMutation.isPending}
          >
            取消
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploadMutation.isPending}
          >
            {uploadMutation.isPending ? '上传中...' : '上传'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
