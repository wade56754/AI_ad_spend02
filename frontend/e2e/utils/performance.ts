/**
 * Chrome DevTools 性能测试工具
 * 使用 Puppeteer 的 Chrome DevTools Protocol (CDP) 进行性能分析
 */

import { Page, CDPSession } from 'puppeteer'
import * as fs from 'fs'
import * as path from 'path'

/**
 * 性能指标接口
 */
export interface PerformanceMetrics {
  // Core Web Vitals
  FCP: number // First Contentful Paint
  LCP: number // Largest Contentful Paint
  CLS: number // Cumulative Layout Shift
  FID?: number // First Input Delay
  TTI: number // Time to Interactive
  TBT: number // Total Blocking Time

  // 其他指标
  domContentLoaded: number
  loadComplete: number
  firstPaint: number

  // 资源统计
  resourceStats: ResourceStats
}

export interface ResourceStats {
  totalRequests: number
  totalSize: number // bytes
  totalDuration: number // ms
  byType: Record<string, { count: number; size: number }>
}

/**
 * 性能测试类
 */
export class PerformanceTester {
  private page: Page
  private cdpSession: CDPSession | null = null

  constructor(page: Page) {
    this.page = page
  }

  /**
   * 启动性能监控
   */
  async startPerformanceMonitoring() {
    this.cdpSession = await this.page.target().createCDPSession()

    // 启用各种 CDP 域
    await this.cdpSession.send('Performance.enable')
    await this.cdpSession.send('Network.enable')
    await this.cdpSession.send('Page.enable')
  }

  /**
   * 停止性能监控
   */
  async stopPerformanceMonitoring() {
    if (this.cdpSession) {
      await this.cdpSession.send('Performance.disable')
      await this.cdpSession.send('Network.disable')
      await this.cdpSession.send('Page.disable')
      await this.cdpSession.detach()
      this.cdpSession = null
    }
  }

  /**
   * 收集性能指标
   */
  async collectPerformanceMetrics(): Promise<PerformanceMetrics> {
    // 等待页面完全加载
    await this.page.waitForLoadState('networkidle')

    // 获取 Performance API 指标
    const metrics = await this.page.evaluate(() => {
      const performance = window.performance
      const timing = performance.timing
      const paintEntries = performance.getEntriesByType('paint')
      const navigationEntries = performance.getEntriesByType(
        'navigation'
      ) as PerformanceNavigationTiming[]

      // Core Web Vitals
      let FCP = 0
      let FP = 0

      paintEntries.forEach((entry) => {
        if (entry.name === 'first-contentful-paint') {
          FCP = entry.startTime
        }
        if (entry.name === 'first-paint') {
          FP = entry.startTime
        }
      })

      // LCP (需要使用 PerformanceObserver，这里简化处理)
      const lcpEntry = performance.getEntriesByType('largest-contentful-paint')[0] as any
      const LCP = lcpEntry ? lcpEntry.renderTime || lcpEntry.loadTime : 0

      // TTI 和 TBT 的简化计算
      const domInteractive = timing.domInteractive - timing.navigationStart
      const domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart
      const loadComplete = timing.loadEventEnd - timing.navigationStart

      return {
        FCP,
        FP,
        LCP,
        domInteractive,
        domContentLoaded,
        loadComplete,
      }
    })

    // 获取资源统计
    const resourceStats = await this.collectResourceStats()

    // 获取 CLS
    const cls = await this.calculateCLS()

    return {
      FCP: metrics.FCP,
      LCP: metrics.LCP,
      CLS: cls,
      TTI: metrics.domInteractive,
      TBT: 0, // 简化处理，实际需要复杂计算
      domContentLoaded: metrics.domContentLoaded,
      loadComplete: metrics.loadComplete,
      firstPaint: metrics.FP,
      resourceStats,
    }
  }

  /**
   * 收集资源统计信息
   */
  private async collectResourceStats(): Promise<ResourceStats> {
    const resources = await this.page.evaluate(() => {
      const entries = performance.getEntriesByType('resource') as PerformanceResourceTiming[]

      return entries.map((entry) => ({
        name: entry.name,
        type: entry.initiatorType,
        size: entry.transferSize || 0,
        duration: entry.duration,
      }))
    })

    const stats: ResourceStats = {
      totalRequests: resources.length,
      totalSize: 0,
      totalDuration: 0,
      byType: {},
    }

    resources.forEach((resource) => {
      stats.totalSize += resource.size
      stats.totalDuration += resource.duration

      if (!stats.byType[resource.type]) {
        stats.byType[resource.type] = { count: 0, size: 0 }
      }

      stats.byType[resource.type].count++
      stats.byType[resource.type].size += resource.size
    })

    return stats
  }

  /**
   * 计算 CLS (Cumulative Layout Shift)
   */
  private async calculateCLS(): Promise<number> {
    const cls = await this.page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsValue = 0

        const observer = new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value
            }
          }
        })

        observer.observe({ type: 'layout-shift', buffered: true })

        // 等待一段时间后返回结果
        setTimeout(() => {
          observer.disconnect()
          resolve(clsValue)
        }, 500)
      })
    })

    return cls
  }

  /**
   * 生成性能报告
   */
  generateReport(metrics: PerformanceMetrics, pageName: string): string {
    const report = `
# 性能测试报告 - ${pageName}

## Core Web Vitals

| 指标 | 值 | 评分 |
|------|-----|------|
| **FCP** (First Contentful Paint) | ${metrics.FCP.toFixed(2)}ms | ${this.scoreMetric('FCP', metrics.FCP)} |
| **LCP** (Largest Contentful Paint) | ${metrics.LCP.toFixed(2)}ms | ${this.scoreMetric('LCP', metrics.LCP)} |
| **CLS** (Cumulative Layout Shift) | ${metrics.CLS.toFixed(4)} | ${this.scoreMetric('CLS', metrics.CLS)} |

## 其他性能指标

| 指标 | 值 |
|------|-----|
| **TTI** (Time to Interactive) | ${metrics.TTI.toFixed(2)}ms |
| **DOM Content Loaded** | ${metrics.domContentLoaded.toFixed(2)}ms |
| **Load Complete** | ${metrics.loadComplete.toFixed(2)}ms |
| **First Paint** | ${metrics.firstPaint.toFixed(2)}ms |

## 资源统计

- **总请求数**: ${metrics.resourceStats.totalRequests}
- **总大小**: ${this.formatBytes(metrics.resourceStats.totalSize)}
- **总耗时**: ${metrics.resourceStats.totalDuration.toFixed(2)}ms

### 按类型分组

${Object.entries(metrics.resourceStats.byType)
  .map(
    ([type, stats]) =>
      `- **${type}**: ${stats.count} 个请求, ${this.formatBytes(stats.size)}`
  )
  .join('\n')}

## 评分说明

- ✅ 优秀: FCP < 1800ms, LCP < 2500ms, CLS < 0.1
- ⚠️  需要改进: FCP 1800-3000ms, LCP 2500-4000ms, CLS 0.1-0.25
- ❌ 差: FCP > 3000ms, LCP > 4000ms, CLS > 0.25

---
生成时间: ${new Date().toISOString()}
`

    return report
  }

  /**
   * 评分指标
   */
  private scoreMetric(metric: string, value: number): string {
    const thresholds: Record<string, { good: number; needsImprovement: number }> = {
      FCP: { good: 1800, needsImprovement: 3000 },
      LCP: { good: 2500, needsImprovement: 4000 },
      CLS: { good: 0.1, needsImprovement: 0.25 },
    }

    const threshold = thresholds[metric]
    if (!threshold) return 'N/A'

    if (value <= threshold.good) {
      return '✅ 优秀'
    } else if (value <= threshold.needsImprovement) {
      return '⚠️  需要改进'
    } else {
      return '❌ 差'
    }
  }

  /**
   * 格式化字节数
   */
  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B'

    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
  }

  /**
   * 保存性能报告到文件
   */
  async saveReport(metrics: PerformanceMetrics, pageName: string) {
    const report = this.generateReport(metrics, pageName)
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const filename = `e2e/reports/performance-${pageName}-${timestamp}.md`

    // 确保目录存在
    const dir = path.dirname(filename)
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }

    fs.writeFileSync(filename, report)
    console.log(`📊 性能报告已保存: ${filename}`)

    return filename
  }

  /**
   * 收集 Network 请求详情
   */
  async collectNetworkRequests(): Promise<any[]> {
    const requests: any[] = []

    this.page.on('request', (request) => {
      requests.push({
        url: request.url(),
        method: request.method(),
        resourceType: request.resourceType(),
        headers: request.headers(),
      })
    })

    this.page.on('response', async (response) => {
      const request = requests.find((r) => r.url === response.url())
      if (request) {
        request.status = response.status()
        request.statusText = response.statusText()
        request.size = (await response.buffer()).length
      }
    })

    return requests
  }

  /**
   * 录制 Performance Timeline
   */
  async recordPerformanceTimeline(duration = 5000): Promise<any> {
    if (!this.cdpSession) {
      await this.startPerformanceMonitoring()
    }

    const timeline: any[] = []

    this.cdpSession?.on('Performance.metrics', (event) => {
      timeline.push({
        timestamp: Date.now(),
        metrics: event.metrics,
      })
    })

    await new Promise((resolve) => setTimeout(resolve, duration))

    return timeline
  }
}

/**
 * 扩展 Page 等待选项
 */
declare module 'puppeteer' {
  interface Page {
    waitForLoadState(state: 'load' | 'domcontentloaded' | 'networkidle'): Promise<void>
  }
}

// 扩展 Page.waitForLoadState 方法
Object.defineProperty(Page.prototype, 'waitForLoadState', {
  value: async function (state: 'load' | 'domcontentloaded' | 'networkidle') {
    const waitUntilMap = {
      load: 'load',
      domcontentloaded: 'domcontentloaded',
      networkidle: 'networkidle0',
    } as const

    await this.waitForNavigation({
      waitUntil: waitUntilMap[state] as any,
      timeout: 30000,
    }).catch(() => {
      // Ignore navigation timeout
    })
  },
})
