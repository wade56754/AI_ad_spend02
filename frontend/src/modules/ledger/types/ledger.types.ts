/**
 * Ledger Types
 *
 * Aligned with:
 * - LEDGER_SOT.md v1.1 (Double-entry bookkeeping)
 * - DATA_SCHEMA.md v5.2 (ledger_entries table)
 */

import type { UUID, ISODateString, Money } from '@/types';

// === Entry Types (LEDGER_SOT.md v1.1 Section 3) ===

/**
 * Ledger entry types - MUST use these exact values
 *
 * RECHARGE: Topup credit (tenant_balance +)
 * CONSUMPTION: Ad spend deduction (tenant_balance -, project_balance -)
 * TRANSFER: Between projects (source -, target +)
 * ADJUSTMENT: Manual correction (admin only)
 * REFUND: Reversal of consumption
 */
export type LedgerEntryType =
  | 'RECHARGE'
  | 'CONSUMPTION'
  | 'TRANSFER'
  | 'ADJUSTMENT'
  | 'REFUND';

// === Entity Types ===

export interface LedgerEntry {
  id: UUID;
  tenant_id: UUID;
  entry_type: LedgerEntryType;

  // Amount (always positive, direction determined by entry_type)
  amount: Money;

  // Account references
  source_project_id?: UUID; // For TRANSFER/CONSUMPTION
  target_project_id?: UUID; // For TRANSFER

  // Balance snapshots (immutable after creation)
  tenant_balance_before: Money;
  tenant_balance_after: Money;
  project_balance_before?: Money;
  project_balance_after?: Money;

  // Reference to source document
  reference_type?: 'topup' | 'daily_report' | 'transfer' | 'manual';
  reference_id?: UUID;

  // Metadata
  description: string;
  created_by: UUID;
  created_at: ISODateString;

  // Immutability marker
  is_locked: boolean;
}

// === Balance Types ===

export interface TenantBalance {
  tenant_id: UUID;
  current_balance: Money;
  total_recharged: Money;
  total_consumed: Money;
  last_entry_at?: ISODateString;
}

export interface ProjectBalance {
  project_id: UUID;
  tenant_id: UUID;
  current_balance: Money;
  total_allocated: Money;
  total_consumed: Money;
  last_entry_at?: ISODateString;
}

// === List/Filter Types ===

export interface LedgerFilters {
  tenant_id?: UUID;
  project_id?: UUID;
  entry_type?: LedgerEntryType | LedgerEntryType[];
  start_date?: string;
  end_date?: string;
  min_amount?: number;
  max_amount?: number;
  reference_type?: 'topup' | 'daily_report' | 'transfer' | 'manual';
}

export interface LedgerListParams extends LedgerFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'amount' | 'entry_type';
  sort_order?: 'asc' | 'desc';
}

// === Entry Type Display Config ===

export const ENTRY_TYPE_CONFIG: Record<LedgerEntryType, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info'; direction: 'in' | 'out' | 'neutral' }> = {
  RECHARGE: { label: '充值', variant: 'success', direction: 'in' },
  CONSUMPTION: { label: '消耗', variant: 'error', direction: 'out' },
  TRANSFER: { label: '转账', variant: 'info', direction: 'neutral' },
  ADJUSTMENT: { label: '调整', variant: 'warning', direction: 'neutral' },
  REFUND: { label: '退款', variant: 'success', direction: 'in' },
};

// === Invariants (LEDGER_SOT.md v1.1 Section 5) ===

/**
 * CRITICAL: These rules are enforced by the backend
 * Frontend should NOT attempt to bypass these
 *
 * 1. ledger_entries is append-only (no UPDATE/DELETE)
 * 2. balance fields MUST NOT be modified directly
 * 3. tenant_balance = SUM(RECHARGE + REFUND - CONSUMPTION - TRANSFER_OUT)
 * 4. project_balance = SUM(ALLOCATION + TRANSFER_IN - CONSUMPTION - TRANSFER_OUT)
 */
export const LEDGER_INVARIANTS = {
  APPEND_ONLY: 'Ledger entries cannot be modified or deleted',
  NO_DIRECT_BALANCE_UPDATE: 'Balance must only change through ledger entries',
  TENANT_BALANCE_FORMULA: 'tenant_balance = SUM(RECHARGE + REFUND - CONSUMPTION)',
  PROJECT_BALANCE_FORMULA: 'project_balance = SUM(ALLOCATION - CONSUMPTION)',
} as const;
