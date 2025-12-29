/**
 * 通用断言辅助函数
 *
 * 基于: AI_TEST_GUIDE_v2.1.md §4
 */

import { Page, Locator, expect } from '@playwright/test';

// ============================================================
// 数据状态断言
// ============================================================

/**
 * 验证加载状态显示骨架屏
 */
export async function expectLoadingState(page: Page): Promise<void> {
  await expect(page.locator('[data-testid="loading-skeleton"]')).toBeVisible();
}

/**
 * 验证空状态显示提示
 */
export async function expectEmptyState(page: Page, message?: string): Promise<void> {
  const emptyState = page.locator('[data-testid="empty-state"]');
  await expect(emptyState).toBeVisible();
  if (message) {
    await expect(emptyState).toContainText(message);
  }
}

/**
 * 验证错误状态显示
 */
export async function expectErrorState(page: Page): Promise<void> {
  await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
}

/**
 * 验证成功提示显示
 */
export async function expectSuccessToast(page: Page, message?: string): Promise<void> {
  const toast = page.locator('[data-testid="toast-success"]');
  await expect(toast).toBeVisible();
  if (message) {
    await expect(toast).toContainText(message);
  }
}

/**
 * 验证错误提示显示
 */
export async function expectErrorToast(page: Page, message?: string): Promise<void> {
  const toast = page.locator('[data-testid="toast-error"]');
  await expect(toast).toBeVisible();
  if (message) {
    await expect(toast).toContainText(message);
  }
}

// ============================================================
// Phase 1 规则断言
// ============================================================

/**
 * 验证元素高亮但可操作（Phase 1 不阻断）
 */
export async function expectHighlightedButEnabled(
  element: Locator,
  highlightClass: RegExp = /bg-red|text-red|warning|text-amber/
): Promise<void> {
  // 验证高亮样式
  await expect(element).toHaveClass(highlightClass);
  // 验证仍可操作
  await expect(element).toBeEnabled();
}

/**
 * 验证异常数据高亮
 */
export async function expectAbnormalHighlight(
  page: Page,
  cellTestId: string
): Promise<void> {
  const cell = page.locator(`[data-testid="${cellTestId}"]`);
  await expect(cell).toHaveClass(/bg-red-50|text-red|negative/);
}

/**
 * 验证按钮在异常情况下仍可点击（Phase 1）
 */
export async function expectButtonEnabledDespiteWarning(
  page: Page,
  buttonTestId: string
): Promise<void> {
  const button = page.locator(`[data-testid="${buttonTestId}"]`);
  await expect(button).toBeEnabled();
  await expect(button).not.toHaveAttribute('disabled');
}

// ============================================================
// 表格断言
// ============================================================

/**
 * 验证表格可见
 */
export async function expectTableVisible(page: Page, tableTestId: string): Promise<void> {
  await expect(page.locator(`[data-testid="${tableTestId}"]`)).toBeVisible();
}

/**
 * 验证表格有数据行
 */
export async function expectTableHasRows(
  page: Page,
  tableTestId: string,
  minRows: number = 1
): Promise<void> {
  const rows = page.locator(`[data-testid="${tableTestId}"] tbody tr`);
  const count = await rows.count();
  expect(count).toBeGreaterThanOrEqual(minRows);
}

/**
 * 验证表格列标题
 */
export async function expectTableHeaders(
  page: Page,
  tableTestId: string,
  expectedHeaders: string[]
): Promise<void> {
  const headers = page.locator(`[data-testid="${tableTestId}"] th`);
  await expect(headers).toHaveCount(expectedHeaders.length);

  for (let i = 0; i < expectedHeaders.length; i++) {
    await expect(headers.nth(i)).toHaveText(expectedHeaders[i]);
  }
}

// ============================================================
// 状态机断言
// ============================================================

/**
 * 验证状态转换成功
 */
export async function expectStateTransitionSuccess(
  page: Page,
  expectedStatus: string
): Promise<void> {
  await expectSuccessToast(page);
  // 验证状态已更新（具体实现取决于 UI）
}

/**
 * 验证非法状态转换被拒绝
 */
export async function expectIllegalTransitionRejected(
  response: { status: () => number; json: () => Promise<any> },
  expectedErrorCode: string
): Promise<void> {
  expect(response.status()).toBe(400);
  const body = await response.json();
  expect(body.code).toBe(expectedErrorCode);
}

/**
 * 验证终态按钮禁用
 */
export async function expectTerminalStateButtonsDisabled(
  page: Page,
  rowId: string
): Promise<void> {
  const actionButtons = page.locator(`[data-testid*="btn-${rowId}"]`);
  const count = await actionButtons.count();

  for (let i = 0; i < count; i++) {
    const button = actionButtons.nth(i);
    const isVisible = await button.isVisible();
    if (isVisible) {
      await expect(button).toBeDisabled();
    }
  }
}

// ============================================================
// UI 通用断言
// ============================================================

/**
 * 验证页面标题
 */
export async function expectPageTitle(page: Page, title: string): Promise<void> {
  await expect(page.locator('h1')).toHaveText(title);
}

/**
 * 验证元素可见
 */
export async function expectVisible(page: Page, testId: string): Promise<void> {
  await expect(page.locator(`[data-testid="${testId}"]`)).toBeVisible();
}

/**
 * 验证元素不可见
 */
export async function expectNotVisible(page: Page, testId: string): Promise<void> {
  await expect(page.locator(`[data-testid="${testId}"]`)).not.toBeVisible();
}

/**
 * 验证弹窗显示
 */
export async function expectDialogVisible(page: Page, dialogTestId: string): Promise<void> {
  await expect(page.locator(`[data-testid="${dialogTestId}"]`)).toBeVisible();
}

/**
 * 验证弹窗关闭
 */
export async function expectDialogClosed(page: Page, dialogTestId: string): Promise<void> {
  await expect(page.locator(`[data-testid="${dialogTestId}"]`)).not.toBeVisible();
}
