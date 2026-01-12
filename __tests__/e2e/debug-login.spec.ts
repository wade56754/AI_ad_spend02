/**
 * Debug test for login flow
 */

import { test, expect } from '@playwright/test';
import { TEST_ACCOUNTS } from '../fixtures/test-accounts';

test('debug login flow', async ({ page }) => {
  // Step 1: Go to login page
  console.log('Step 1: Navigate to login page');
  await page.goto('/login');
  await page.waitForSelector('[data-testid="email-input"]');
  console.log('Login page loaded');

  // Step 2: Fill in credentials
  console.log('Step 2: Filling in credentials');
  const account = TEST_ACCOUNTS['ceo'];
  await page.fill('[data-testid="email-input"]', account.email);
  await page.fill('[data-testid="password-input"]', account.password);
  console.log(`Filled: ${account.email}`);

  // Step 3: Click login button
  console.log('Step 3: Clicking login button');
  await page.click('[data-testid="login-button"]', { force: true });

  // Step 4: Wait for navigation away from login
  console.log('Step 4: Waiting for navigation');
  try {
    await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 });
    console.log(`Current URL after login: ${page.url()}`);
  } catch (e) {
    console.log(`Navigation failed, current URL: ${page.url()}`);
    // Take screenshot for debugging
    await page.screenshot({ path: 'debug-login-failed.png' });
    throw e;
  }

  // Step 5: Check localStorage
  console.log('Step 5: Checking localStorage');
  const authState = await page.evaluate(() => {
    return {
      authToken: localStorage.getItem('auth-token'),
      authUser: localStorage.getItem('auth-user'),
      cookie: document.cookie,
    };
  });
  console.log('Auth state:', JSON.stringify(authState, null, 2));

  // Step 5.5: Check Playwright context cookies before goto
  console.log('Step 5.5: Checking Playwright context cookies');
  const contextCookies = await page.context().cookies();
  console.log('Context cookies:', JSON.stringify(contextCookies, null, 2));

  // Ensure cookies are synced to context
  if (!contextCookies.find(c => c.name === 'access_token')) {
    console.log('Cookie not in context, manually adding...');
    const token = await page.evaluate(() => {
      const match = document.cookie.match(/access_token=([^;]+)/);
      return match ? match[1] : null;
    });
    if (token) {
      await page.context().addCookies([{
        name: 'access_token',
        value: token,
        domain: 'localhost',
        path: '/',
      }]);
      console.log('Cookie added to context');
    }
  }

  const contextCookiesAfter = await page.context().cookies();
  console.log('Context cookies after sync:', JSON.stringify(contextCookiesAfter, null, 2));

  // Step 6: Try page.goto to same URL with waitUntil: 'commit'
  console.log('Step 6: Navigating with page.goto()');
  console.log('Current URL before goto:', page.url());

  // Don't navigate if already at the right URL
  if (page.url() === 'http://localhost:3000/') {
    console.log('Already at /, skipping goto');
    // Just wait for content
    await page.waitForLoadState('networkidle');
  } else {
    await page.goto('/', { waitUntil: 'commit' });
    await page.waitForLoadState('networkidle');
  }
  console.log(`URL after goto: ${page.url()}`);

  // Step 7: Check if still authenticated
  const authStateAfterGoto = await page.evaluate(() => {
    return {
      authToken: localStorage.getItem('auth-token'),
      authUser: localStorage.getItem('auth-user'),
      cookie: document.cookie,
    };
  });
  console.log('Auth state after goto:', JSON.stringify(authStateAfterGoto, null, 2));

  // Step 8: Check if h1 is visible
  const h1 = page.locator('h1');
  const h1Text = await h1.textContent().catch(() => 'not found');
  console.log(`H1 text: ${h1Text}`);

  // Final check
  const currentUrl = page.url();
  console.log(`Final URL: ${currentUrl}`);

  if (currentUrl.includes('/login')) {
    console.log('PROBLEM: Redirected back to login!');
    await page.screenshot({ path: 'debug-redirected-to-login.png' });
  }

  // This should pass
  await expect(h1).toBeVisible();
});
