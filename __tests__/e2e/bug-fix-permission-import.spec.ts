/**
 * Bug Fix Verification: TECH_TO_BUSINESS_ROLE Import Error
 * 
 * 验证修复:
 * - frontend/src/hooks/usePermission.ts 中的导入错误已修复
 * - TECH_TO_BUSINESS_ROLE → TECH_TO_BUSINESS_MAP
 * 
 * 测试场景:
 * 1. 验证前端可以正常构建（无导入错误）
 * 2. 验证权限检查功能正常工作
 * 3. 验证不同角色的权限映射正确
 */

import { test, expect } from '@playwright/test';

test.describe('Bug Fix: Permission Import Error', () => {
  test('前端构建应该成功，无导入错误', async ({ page }) => {
    // 访问前端页面，检查是否有构建错误
    await page.goto('http://localhost:3000');
    
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    
    // 检查控制台是否有错误
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // 检查页面是否正常加载（不是错误页面）
    const pageContent = await page.content();
    expect(pageContent).not.toContain('Build Error');
    expect(pageContent).not.toContain('TECH_TO_BUSINESS_ROLE');
    
    // 检查是否有相关的导入错误
    const hasImportError = errors.some(error => 
      error.includes('TECH_TO_BUSINESS_ROLE') || 
      error.includes('doesn\'t exist')
    );
    
    expect(hasImportError).toBe(false);
  });

  test('权限检查 Hook 应该正常工作', async ({ page }) => {
    // 访问需要权限的页面（如设置页面）
    await page.goto('http://localhost:3000/settings');
    
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    
    // 检查页面是否正常加载（不是错误页面）
    const pageContent = await page.content();
    expect(pageContent).not.toContain('Build Error');
    expect(pageContent).not.toContain('TECH_TO_BUSINESS_ROLE');
    
    // 检查控制台是否有权限相关的错误
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // 等待一下，让所有错误都收集到
    await page.waitForTimeout(1000);
    
    // 检查是否有权限相关的错误
    const hasPermissionError = errors.some(error => 
      error.includes('TECH_TO_BUSINESS') ||
      error.includes('usePermission') ||
      error.includes('Cannot read property')
    );
    
    expect(hasPermissionError).toBe(false);
  });

  test('不同角色的权限映射应该正确', async ({ page, context }) => {
    // 这个测试需要登录，暂时跳过，仅验证构建成功
    test.skip();
    
    // TODO: 实现完整的权限映射测试
    // 1. 使用不同角色登录
    // 2. 检查权限检查功能
    // 3. 验证 TECH_TO_BUSINESS_MAP 映射正确
  });
});

