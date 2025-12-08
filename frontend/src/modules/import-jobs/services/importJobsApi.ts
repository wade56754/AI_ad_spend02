/**
 * Import Jobs API Service
 *
 * SoT 对齐: API_SOT.md v9.0
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type {
  ImportJob,
  ImportJobProgress,
  ImportJobStatistics,
  ImportJobListParams,
} from '../types';

const BASE_URL = '/api/import_jobs';

/** 获取导入任务列表 */
export async function getImportJobs(params?: ImportJobListParams) {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.status) searchParams.set('status', params.status);
  if (params?.type) searchParams.set('type', params.type);

  const query = searchParams.toString();
  return apiFetchPaginated<ImportJob>(`${BASE_URL}${query ? `?${query}` : ''}`);
}

/** 获取导入任务详情 */
export async function getImportJob(id: number) {
  return apiFetch<ImportJob>(`${BASE_URL}/${id}`);
}

/** 获取导入任务进度 */
export async function getImportJobProgress(id: number) {
  return apiFetch<ImportJobProgress>(`${BASE_URL}/${id}/progress`);
}

/** 获取导入任务统计 */
export async function getImportJobStatistics() {
  return apiFetch<ImportJobStatistics>(`${BASE_URL}/statistics`);
}

/** 开始处理导入任务 (pending → processing) */
export async function startImportJob(id: number) {
  return apiFetch<ImportJob>(`${BASE_URL}/${id}/start`, {
    method: 'POST',
  });
}

/** 取消导入任务 (pending → cancelled) */
export async function cancelImportJob(id: number) {
  return apiFetch<ImportJob>(`${BASE_URL}/${id}/cancel`, {
    method: 'POST',
  });
}

/** 删除导入任务 (仅admin，仅pending) */
export async function deleteImportJob(id: number) {
  return apiFetch<void>(`${BASE_URL}/${id}`, {
    method: 'DELETE',
  });
}

/** 上传导入文件 */
export async function uploadImportFile(file: File, jobType: string) {
  const formData = new FormData();
  formData.append('file', file);

  // 注意: 使用原生fetch处理FormData上传，不设置Content-Type让浏览器自动设置
  const response = await fetch(`${BASE_URL}/upload?job_type=${jobType}`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || '上传失败');
  }

  return response.json();
}

/** 检查文件重复 */
export async function checkDuplicateFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BASE_URL}/check-duplicate`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || '检查失败');
  }

  return response.json();
}
