/**
 * Suppliers API Service
 *
 * SoT 对齐:
 * - DATA_SCHEMA.md v5.2 (supplier entity)
 * - backend/routers/suppliers.py
 */

import { apiFetch, apiFetchPaginated } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/api';
import type {
  Supplier,
  SupplierListParams,
  SupplierCreateInput,
  SupplierUpdateInput,
  SupplierStatistics,
  SupplierLedgerSummary,
  SupplierAccount,
} from '../types/supplier.types';

const BASE_PATH = '/api/v1/suppliers';

// ========== Query Functions ==========

/**
 * Get paginated list of suppliers
 * GET /api/v1/suppliers
 */
export async function getSuppliers(
  params: SupplierListParams = {}
): Promise<PaginatedResponse<Supplier>> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.status) searchParams.set('status', params.status);
  if (params.search) searchParams.set('search', params.search);
  if (params.base_currency) searchParams.set('base_currency', params.base_currency);
  if (params.payment_method) searchParams.set('payment_method', params.payment_method);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  const url = query ? `${BASE_PATH}?${query}` : BASE_PATH;

  return apiFetchPaginated<Supplier>(url);
}

/**
 * Get single supplier by ID
 * GET /api/v1/suppliers/:id
 */
export async function getSupplier(id: number): Promise<Supplier> {
  return apiFetch<Supplier>(`${BASE_PATH}/${id}`);
}

/**
 * Get supplier statistics
 * GET /api/v1/suppliers/statistics
 */
export async function getSupplierStatistics(): Promise<SupplierStatistics> {
  return apiFetch<SupplierStatistics>(`${BASE_PATH}/statistics`);
}

/**
 * Get supplier's related accounts
 * GET /api/v1/suppliers/:id/accounts
 */
export async function getSupplierAccounts(
  supplierId: number,
  params: { page?: number; page_size?: number } = {}
): Promise<PaginatedResponse<SupplierAccount>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));

  const query = searchParams.toString();
  const url = query
    ? `${BASE_PATH}/${supplierId}/accounts?${query}`
    : `${BASE_PATH}/${supplierId}/accounts`;

  return apiFetchPaginated<SupplierAccount>(url);
}

/**
 * Get supplier's ledger summary
 * GET /api/v1/suppliers/:id/ledger-summary
 */
export async function getSupplierLedgerSummary(
  supplierId: number
): Promise<SupplierLedgerSummary> {
  return apiFetch<SupplierLedgerSummary>(`${BASE_PATH}/${supplierId}/ledger-summary`);
}

// ========== Mutation Functions ==========

/**
 * Create new supplier
 * POST /api/v1/suppliers
 */
export async function createSupplier(
  input: SupplierCreateInput
): Promise<Supplier> {
  return apiFetch<Supplier>(BASE_PATH, {
    method: 'POST',
    body: input,
  });
}

/**
 * Update supplier
 * PUT /api/v1/suppliers/:id
 */
export async function updateSupplier(
  id: number,
  input: SupplierUpdateInput
): Promise<Supplier> {
  return apiFetch<Supplier>(`${BASE_PATH}/${id}`, {
    method: 'PUT',
    body: input,
  });
}

/**
 * Delete supplier
 * DELETE /api/v1/suppliers/:id
 */
export async function deleteSupplier(id: number): Promise<void> {
  await apiFetch<void>(`${BASE_PATH}/${id}`, {
    method: 'DELETE',
  });
}

// ========== Status Actions ==========

/**
 * Activate supplier
 * PUT /api/v1/suppliers/:id with status: active
 */
export async function activateSupplier(id: number): Promise<Supplier> {
  return updateSupplier(id, { status: 'active' as const });
}

/**
 * Deactivate supplier
 * PUT /api/v1/suppliers/:id with status: inactive
 */
export async function deactivateSupplier(id: number): Promise<Supplier> {
  return updateSupplier(id, { status: 'inactive' as const });
}

/**
 * Suspend supplier
 * PUT /api/v1/suppliers/:id with status: suspended
 */
export async function suspendSupplier(id: number): Promise<Supplier> {
  return updateSupplier(id, { status: 'suspended' as const });
}
