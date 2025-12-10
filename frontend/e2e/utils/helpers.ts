/**
 * E2E 测试辅助工具函数
 */

import { Page, Browser, ElementHandle } from 'puppeteer'

/**
 * 等待导航完成并加载完毕
 */
export async function waitForNavigation(page: Page, timeout = 30000) {
  await page.waitForNavigation({
    waitUntil: ['domcontentloaded', 'networkidle0'],
    timeout,
  })
}

/**
 * 等待元素出现
 */
export async function waitForElement(
  page: Page,
  selector: string,
  timeout = 10000
): Promise<ElementHandle<Element>> {
  await page.waitForSelector(selector, { timeout, visible: true })
  const element = await page.$(selector)
  if (!element) {
    throw new Error(`元素未找到: ${selector}`)
  }
  return element
}

/**
 * 等待文本出现
 */
export async function waitForText(page: Page, text: string, timeout = 10000) {
  await page.waitForFunction(
    (searchText) => document.body.textContent?.includes(searchText),
    { timeout },
    text
  )
}

/**
 * 点击元素并等待导航
 */
export async function clickAndWaitForNavigation(
  page: Page,
  selector: string,
  timeout = 30000
) {
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle0', timeout }),
    page.click(selector),
  ])
}

/**
 * 填写表单字段
 */
export async function fillInput(page: Page, selector: string, value: string) {
  await page.waitForSelector(selector, { visible: true })
  await page.click(selector, { clickCount: 3 }) // 选中所有文本
  await page.keyboard.press('Backspace') // 清空
  await page.type(selector, value, { delay: 10 }) // 输入新值
}

/**
 * 截图（用于调试）
 */
export async function takeScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const filename = `e2e/screenshots/${name}-${timestamp}.png`
  await page.screenshot({ path: filename, fullPage: true })
  console.log(`📸 截图已保存: ${filename}`)
  return filename
}

/**
 * 获取元素文本内容
 */
export async function getText(page: Page, selector: string): Promise<string> {
  const element = await waitForElement(page, selector)
  const text = await page.evaluate((el) => el.textContent || '', element)
  return text.trim()
}

/**
 * 检查元素是否存在
 */
export async function elementExists(page: Page, selector: string): Promise<boolean> {
  try {
    await page.waitForSelector(selector, { timeout: 2000 })
    return true
  } catch {
    return false
  }
}

/**
 * 检查元素是否可见
 */
export async function isElementVisible(page: Page, selector: string): Promise<boolean> {
  try {
    const element = await page.$(selector)
    if (!element) return false

    return await page.evaluate((el) => {
      const style = window.getComputedStyle(el)
      return (
        style.display !== 'none' &&
        style.visibility !== 'hidden' &&
        style.opacity !== '0'
      )
    }, element)
  } catch {
    return false
  }
}

/**
 * 滚动到元素位置
 */
export async function scrollToElement(page: Page, selector: string) {
  const element = await waitForElement(page, selector)
  await page.evaluate((el) => {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, element)
  await page.waitForTimeout(500) // 等待滚动完成
}

/**
 * 等待 API 请求完成
 */
export async function waitForApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  timeout = 30000
) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`等待 API 响应超时: ${urlPattern}`))
    }, timeout)

    page.on('response', async (response) => {
      const url = response.url()
      const matches =
        typeof urlPattern === 'string'
          ? url.includes(urlPattern)
          : urlPattern.test(url)

      if (matches) {
        clearTimeout(timer)
        try {
          const data = await response.json()
          resolve(data)
        } catch {
          resolve(response)
        }
      }
    })
  })
}

/**
 * Mock API 响应
 */
export async function mockApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  mockData: any,
  status = 200
) {
  await page.setRequestInterception(true)

  page.on('request', (request) => {
    const url = request.url()
    const matches =
      typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url)

    if (matches) {
      request.respond({
        status,
        contentType: 'application/json',
        body: JSON.stringify(mockData),
      })
    } else {
      request.continue()
    }
  })
}

/**
 * 清除浏览器存储（Cookie、LocalStorage 等）
 */
export async function clearBrowserStorage(page: Page) {
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
  await page.deleteCookie(...(await page.cookies()))
}

/**
 * 设置 LocalStorage
 */
export async function setLocalStorage(page: Page, key: string, value: string) {
  await page.evaluate(
    (k, v) => {
      localStorage.setItem(k, v)
    },
    key,
    value
  )
}

/**
 * 获取 LocalStorage
 */
export async function getLocalStorage(page: Page, key: string): Promise<string | null> {
  return await page.evaluate((k) => localStorage.getItem(k), key)
}

/**
 * 等待加载指示器消失
 */
export async function waitForLoadingToFinish(page: Page, timeout = 30000) {
  try {
    // 等待常见的加载指示器消失
    await page.waitForFunction(
      () => {
        const loadingElements = document.querySelectorAll(
          '[data-loading="true"], .loading, .spinner'
        )
        return loadingElements.length === 0
      },
      { timeout }
    )
  } catch {
    // 如果没有找到加载指示器，继续执行
  }
}

/**
 * 执行并测量性能
 */
export async function measurePerformance(page: Page, action: () => Promise<void>) {
  const startTime = Date.now()
  await action()
  const endTime = Date.now()
  const duration = endTime - startTime

  console.log(`⏱️  操作耗时: ${duration}ms`)
  return duration
}
