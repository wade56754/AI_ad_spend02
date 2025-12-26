# AI 驱动前端测试框架 v1.0

> **核心问题**: 如何让 Claude 使用 Playwright 执行测试时保证准确性和完整性？
> **解决方案**: 规格书驱动 + 检查点清单 + 双重验证 + 追溯矩阵

---

## 第一章 问题分析

### 1.1 AI 执行测试的挑战

| 挑战 | 问题描述 | 解决方案 |
|------|----------|----------|
| **准确性** | AI 可能误判测试结果 | 双重验证机制 |
| **完整性** | AI 可能遗漏测试场景 | 规格书驱动 + 追溯矩阵 |
| **一致性** | 不同执行结果不一致 | 确定性断言 + 等待策略 |
| **可追溯** | 不知道测了什么 | 测试报告 + 检查点清单 |

### 1.2 解决方案架构

```
┌─────────────────────────────────────────────────────────────────┐
│                   AI 驱动测试框架                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌───────────┐      ┌───────────┐      ┌───────────┐          │
│   │  规格书   │ ──→  │ 检查点    │ ──→  │ 测试脚本  │          │
│   │ (SoT)    │      │ 清单      │      │           │          │
│   └───────────┘      └───────────┘      └───────────┘          │
│         │                  │                  │                 │
│         ↓                  ↓                  ↓                 │
│   ┌───────────┐      ┌───────────┐      ┌───────────┐          │
│   │ 追溯矩阵  │ ←──  │ 测试报告  │ ←──  │ 执行结果  │          │
│   │           │      │           │      │           │          │
│   └───────────┘      └───────────┘      └───────────┘          │
│                                                                 │
│   ══════════════════════════════════════════════════════════   │
│                        双重验证层                               │
│   ┌───────────┐      ┌───────────┐      ┌───────────┐          │
│   │ 视觉验证  │      │ 数据验证  │      │ 状态验证  │          │
│   │ Screenshot│      │ API Mock │      │ DOM 断言 │          │
│   └───────────┘      └───────────┘      └───────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第二章 规格书驱动测试

### 2.1 核心原则

```yaml
原则:
  1. 每个测试用例必须追溯到规格书
  2. 每个规格书检查点必须有对应测试
  3. 测试结果必须可验证、可重现
  4. AI 不能"发明"测试，只能"执行"规格书定义的测试
```

### 2.2 规格书 → 检查点 → 测试用例

```
┌──────────────────────────────────────────────────────────────────┐
│ 规格书: B2-daily-report-review.md                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ §1 模块概述                                                      │
│   ├── 业务目标: 主管审核投手日报                                  │
│   └── 用户角色: supervisor, ceo                                  │
│         │                                                        │
│         ↓                                                        │
│   ┌─────────────────────────────────────────┐                   │
│   │ 检查点 CP-B2-001: 权限验证               │                   │
│   │ - supervisor 可访问 ✓                    │                   │
│   │ - ceo 可访问 ✓                           │                   │
│   │ - pitcher 不可访问 ✓                     │                   │
│   │ - finance 不可访问 ✓                     │                   │
│   └─────────────────────────────────────────┘                   │
│         │                                                        │
│         ↓                                                        │
│   ┌─────────────────────────────────────────┐                   │
│   │ 测试用例 TC-B2-001-01                    │                   │
│   │ 前置: 以 supervisor 登录                 │                   │
│   │ 步骤: 访问 /daily-reports/review         │                   │
│   │ 断言: URL = /daily-reports/review        │                   │
│   │       页面标题包含 "日报审核"             │                   │
│   └─────────────────────────────────────────┘                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 检查点清单模板

每个模块必须有对应的检查点清单：

```yaml
# checkpoints/B2-daily-report-review.yaml

module: B2-daily-report-review
spec_file: docs/5.module-specs/B2-daily-report-review.md
version: "1.0"

checkpoints:
  # ========== 权限检查点 ==========
  - id: CP-B2-001
    category: permission
    description: 页面访问权限
    spec_ref: "§1.2 用户角色"
    cases:
      - role: supervisor
        action: access
        expected: allowed
      - role: ceo
        action: access
        expected: allowed
      - role: pitcher
        action: access
        expected: denied
      - role: finance
        action: access
        expected: denied
      - role: project_owner
        action: access
        expected: denied
      - role: account_manager
        action: access
        expected: denied
      - role: admin
        action: access
        expected: denied

  # ========== UI 检查点 ==========
  - id: CP-B2-002
    category: ui
    description: 页面元素渲染
    spec_ref: "§3 UI 规范"
    cases:
      - element: page_title
        selector: "h1"
        expected_text: "日报审核"
      - element: data_table
        selector: "[data-testid='daily-reports-table']"
        expected: visible
      - element: status_filter
        selector: "[data-testid='status-filter']"
        expected: visible

  # ========== 数据检查点 ==========
  - id: CP-B2-003
    category: data
    description: 数据加载与显示
    spec_ref: "§2 数据需求"
    cases:
      - scenario: loading_state
        expected: "显示加载骨架屏"
      - scenario: empty_state
        expected: "显示'暂无待审核日报'"
      - scenario: data_loaded
        expected: "显示日报列表"
        required_columns:
          - 日期
          - 项目
          - 投手
          - 进粉数
          - 消耗
          - CPL
          - 状态
          - 操作

  # ========== 功能检查点 ==========
  - id: CP-B2-004
    category: function
    description: 审核操作
    spec_ref: "§5 API 接口"
    cases:
      - action: approve
        expected_status: trend_ok
        expected_toast: "审核通过"
      - action: reject
        expected_status: trend_flagged
        expected_toast: "已驳回"

  # ========== Phase 1 检查点 ==========
  - id: CP-B2-005
    category: phase1
    description: Phase 1 规则验证
    spec_ref: "MASTER.md §3.1"
    cases:
      - scenario: abnormal_cpl
        expected: "数据高亮，但审核按钮可点击"
      - scenario: missing_data
        expected: "警告提示，但审核按钮可点击"

# 追溯统计
summary:
  total_checkpoints: 5
  total_cases: 20
  coverage:
    permission: 7 cases
    ui: 3 cases
    data: 4 cases
    function: 2 cases
    phase1: 2 cases
```

---

## 第三章 AI 测试执行协议

### 3.1 执行前协议

AI 执行测试前必须完成以下步骤：

```markdown
## AI 测试执行前检查清单

### Step 1: 加载检查点清单
□ 读取 checkpoints/{module}.yaml
□ 确认检查点数量: X 个
□ 确认测试用例数量: Y 个

### Step 2: 验证测试环境
□ 前端服务运行中 (http://localhost:3000)
□ Mock API 服务运行中
□ 测试账号可用（7 个角色账号）

### Step 3: 输出执行计划
格式:
```
执行计划: {module}
检查点: {count} 个
测试用例: {count} 个
预计耗时: {minutes} 分钟
```

### Step 4: 确认执行
等待用户确认后开始执行
```

### 3.2 执行中协议

```typescript
// AI 执行测试的标准流程

interface TestExecutionProtocol {
  // 1. 每个测试用例必须输出
  beforeTest: {
    checkpoint_id: string;      // CP-B2-001
    case_id: string;            // TC-B2-001-01
    description: string;        // "supervisor 访问日报审核页"
    expected: string;           // "成功访问，显示页面"
  };

  // 2. 执行步骤必须记录
  steps: Array<{
    action: string;             // "点击登录按钮"
    selector?: string;          // "button[type='submit']"
    input?: string;             // "supervisor@test.com"
    screenshot?: boolean;       // true = 截图
  }>;

  // 3. 断言必须明确
  assertions: Array<{
    type: 'url' | 'text' | 'element' | 'api' | 'screenshot';
    expected: string;
    actual: string;
    result: 'PASS' | 'FAIL';
  }>;

  // 4. 结果必须输出
  afterTest: {
    result: 'PASS' | 'FAIL';
    duration: number;           // 执行时间（秒）
    screenshot?: string;        // 截图路径
    error?: string;             // 失败原因
  };
}
```

### 3.3 AI 执行输出格式

```markdown
## 测试执行: TC-B2-001-01

### 检查点
- ID: CP-B2-001
- 描述: supervisor 访问日报审核页
- 规格书引用: B2-daily-report-review.md §1.2

### 执行步骤
1. ✓ 访问 /login
2. ✓ 输入邮箱: supervisor@test.com
3. ✓ 输入密码: ******
4. ✓ 点击登录按钮
5. ✓ 等待跳转完成
6. ✓ 访问 /daily-reports/review

### 断言验证
| 断言类型 | 预期 | 实际 | 结果 |
|----------|------|------|------|
| URL | /daily-reports/review | /daily-reports/review | ✅ PASS |
| 文本 | 包含"日报审核" | "日报审核" | ✅ PASS |
| 元素 | 表格可见 | 可见 | ✅ PASS |

### 结果
- 状态: ✅ PASS
- 耗时: 3.2s
- 截图: screenshots/TC-B2-001-01.png
```

---

## 第四章 双重验证机制

### 4.1 验证层级

```
┌─────────────────────────────────────────────────────────────────┐
│                      双重验证机制                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  第一层: 自动断言                                               │
│  ─────────────────                                              │
│  • URL 断言: expect(page).toHaveURL('/expected')                │
│  • 文本断言: expect(locator).toHaveText('expected')             │
│  • 元素断言: expect(locator).toBeVisible()                      │
│  • API 断言: 验证 Mock API 调用                                 │
│                                                                 │
│  第二层: 视觉验证（截图对比）                                   │
│  ─────────────────                                              │
│  • 每个关键步骤截图                                             │
│  • 与基准截图对比                                               │
│  • 差异超过阈值则标记                                           │
│                                                                 │
│  第三层: 人工确认（关键路径）                                   │
│  ─────────────────                                              │
│  • E2E 测试完成后输出截图报告                                   │
│  • 人工确认关键页面截图                                         │
│  • 异常情况人工复核                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 确定性断言规则

AI 必须使用确定性断言，避免模糊判断：

```typescript
// ✅ 确定性断言（AI 必须使用）

// URL 精确匹配
await expect(page).toHaveURL('/daily-reports/review');

// 文本精确匹配
await expect(page.locator('h1')).toHaveText('日报审核');

// 元素存在性
await expect(page.locator('[data-testid="table"]')).toBeVisible();

// 元素数量
await expect(page.locator('tr')).toHaveCount(10);

// API 调用验证
expect(mockApi.calls).toContainEqual({
  method: 'GET',
  url: '/api/v1/daily-reports',
});

// ❌ 模糊断言（AI 禁止使用）

// 禁止：包含判断（可能误判）
// expect(text).toContain('日报');

// 禁止：正则匹配（不确定）
// expect(text).toMatch(/日报.*/);

// 禁止：主观判断
// expect(element).toBeLargeEnough();
```

### 4.3 等待策略（避免时序问题）

```typescript
// AI 必须使用的等待策略

// 1. 等待 URL 变化
await page.waitForURL('/daily-reports/review');

// 2. 等待元素出现
await page.waitForSelector('[data-testid="table"]');

// 3. 等待加载完成
await page.waitForLoadState('networkidle');

// 4. 等待 API 响应
await page.waitForResponse(
  response => response.url().includes('/api/v1/daily-reports')
);

// 5. 等待状态变化
await expect(page.locator('[data-testid="status"]'))
  .toHaveText('已通过', { timeout: 5000 });

// ❌ 禁止：硬编码等待
// await page.waitForTimeout(3000);
```

### 4.4 截图验证策略

```typescript
// 截图验证配置

const screenshotConfig = {
  // 关键步骤截图
  capturePoints: [
    'before_login',
    'after_login',
    'page_loaded',
    'form_filled',
    'after_submit',
    'final_state',
  ],

  // 截图命名规则
  naming: '{testId}_{step}_{timestamp}.png',

  // 存储位置
  outputDir: 'test-results/screenshots',

  // 全页面截图
  fullPage: true,
};

// AI 执行时的截图代码
async function captureStep(page: Page, testId: string, step: string) {
  const filename = `${testId}_${step}_${Date.now()}.png`;
  await page.screenshot({
    path: `test-results/screenshots/${filename}`,
    fullPage: true,
  });
  return filename;
}
```

---

## 第五章 追溯矩阵

### 5.1 追溯矩阵结构

```yaml
# traceability/B2-daily-report-review.yaml

module: B2-daily-report-review
generated_at: "2024-12-23T10:00:00Z"
generated_by: "Claude"

# 规格书 → 检查点 → 测试用例 追溯
traceability:
  - spec_section: "§1.2 用户角色"
    checkpoints:
      - id: CP-B2-001
        test_cases:
          - TC-B2-001-01  # supervisor 访问
          - TC-B2-001-02  # ceo 访问
          - TC-B2-001-03  # pitcher 拒绝
          - TC-B2-001-04  # finance 拒绝
        coverage: 100%  # 7/7 角色已测试

  - spec_section: "§3 UI 规范"
    checkpoints:
      - id: CP-B2-002
        test_cases:
          - TC-B2-002-01  # 页面标题
          - TC-B2-002-02  # 数据表格
          - TC-B2-002-03  # 状态筛选
        coverage: 100%

  - spec_section: "§5 API 接口"
    checkpoints:
      - id: CP-B2-004
        test_cases:
          - TC-B2-004-01  # 审核通过
          - TC-B2-004-02  # 审核驳回
        coverage: 100%

# 覆盖率统计
coverage_summary:
  spec_sections: 5
  checkpoints: 5
  test_cases: 20
  overall_coverage: 100%

# 未覆盖项（必须为空）
uncovered:
  spec_sections: []
  checkpoints: []
```

### 5.2 AI 必须输出的追溯报告

```markdown
## 测试追溯报告: B2-daily-report-review

### 1. 执行摘要
- 模块: 日报审核
- 规格书: docs/5.module-specs/B2-daily-report-review.md
- 执行时间: 2024-12-23 10:00:00
- 执行者: Claude

### 2. 覆盖率统计

| 类别 | 总数 | 已测试 | 覆盖率 |
|------|------|--------|--------|
| 规格书章节 | 5 | 5 | 100% |
| 检查点 | 5 | 5 | 100% |
| 测试用例 | 20 | 20 | 100% |
| 7 角色权限 | 7 | 7 | 100% |

### 3. 测试结果

| 检查点 | 用例数 | 通过 | 失败 | 跳过 |
|--------|--------|------|------|------|
| CP-B2-001 权限 | 7 | 7 | 0 | 0 |
| CP-B2-002 UI | 3 | 3 | 0 | 0 |
| CP-B2-003 数据 | 4 | 4 | 0 | 0 |
| CP-B2-004 功能 | 2 | 2 | 0 | 0 |
| CP-B2-005 Phase1 | 2 | 2 | 0 | 0 |
| **合计** | **20** | **20** | **0** | **0** |

### 4. 追溯矩阵

| 规格书章节 | 检查点 | 测试用例 | 结果 |
|------------|--------|----------|------|
| §1.2 用户角色 | CP-B2-001 | TC-001~007 | ✅ |
| §3 UI 规范 | CP-B2-002 | TC-008~010 | ✅ |
| §2 数据需求 | CP-B2-003 | TC-011~014 | ✅ |
| §5 API 接口 | CP-B2-004 | TC-015~016 | ✅ |
| MASTER §3.1 | CP-B2-005 | TC-017~018 | ✅ |

### 5. 未覆盖项
无

### 6. 截图清单
- screenshots/TC-B2-001-01_login.png
- screenshots/TC-B2-001-01_page_loaded.png
- screenshots/TC-B2-004-01_before_approve.png
- screenshots/TC-B2-004-01_after_approve.png
... (共 40 张截图)

### 7. 结论
✅ 所有检查点已覆盖，所有测试通过
```

---

## 第六章 AI 测试执行脚本

### 6.1 测试执行器

```typescript
// tests/ai-test-executor.ts

import { test, expect, Page } from '@playwright/test';
import * as yaml from 'js-yaml';
import * as fs from 'fs';

interface Checkpoint {
  id: string;
  category: string;
  description: string;
  spec_ref: string;
  cases: TestCase[];
}

interface TestCase {
  role?: string;
  action?: string;
  expected: string;
  selector?: string;
  expected_text?: string;
}

interface TestResult {
  checkpoint_id: string;
  case_index: number;
  description: string;
  expected: string;
  actual: string;
  result: 'PASS' | 'FAIL';
  screenshot?: string;
  error?: string;
  duration: number;
}

// 测试账号配置
const TEST_ACCOUNTS: Record<string, { email: string; password: string }> = {
  ceo: { email: 'ceo@test.com', password: 'test123' },
  finance: { email: 'finance@test.com', password: 'test123' },
  supervisor: { email: 'supervisor@test.com', password: 'test123' },
  pitcher: { email: 'pitcher@test.com', password: 'test123' },
  project_owner: { email: 'owner@test.com', password: 'test123' },
  account_manager: { email: 'am@test.com', password: 'test123' },
  admin: { email: 'admin@test.com', password: 'test123' },
};

/**
 * AI 测试执行器
 * 读取检查点清单，执行测试，输出追溯报告
 */
export class AITestExecutor {
  private page: Page;
  private results: TestResult[] = [];
  private screenshots: string[] = [];

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * 加载检查点清单
   */
  loadCheckpoints(moduleName: string): Checkpoint[] {
    const filePath = `checkpoints/${moduleName}.yaml`;
    const content = fs.readFileSync(filePath, 'utf-8');
    const data = yaml.load(content) as { checkpoints: Checkpoint[] };
    return data.checkpoints;
  }

  /**
   * 执行登录
   */
  async login(role: string): Promise<void> {
    const account = TEST_ACCOUNTS[role];
    if (!account) throw new Error(`Unknown role: ${role}`);

    await this.page.goto('/login');
    await this.page.fill('[name="email"]', account.email);
    await this.page.fill('[name="password"]', account.password);
    await this.page.click('button[type="submit"]');
    await this.page.waitForURL('/', { timeout: 5000 }).catch(() => {});
  }

  /**
   * 执行登出
   */
  async logout(): Promise<void> {
    await this.page.goto('/logout');
    await this.page.waitForURL('/login');
  }

  /**
   * 截图
   */
  async capture(testId: string, step: string): Promise<string> {
    const filename = `${testId}_${step}_${Date.now()}.png`;
    const path = `test-results/screenshots/${filename}`;
    await this.page.screenshot({ path, fullPage: true });
    this.screenshots.push(path);
    return path;
  }

  /**
   * 执行权限测试
   */
  async executePermissionTest(
    checkpoint: Checkpoint,
    targetPath: string
  ): Promise<void> {
    for (let i = 0; i < checkpoint.cases.length; i++) {
      const testCase = checkpoint.cases[i];
      const startTime = Date.now();

      try {
        // 登录
        await this.login(testCase.role!);

        // 访问目标页面
        await this.page.goto(targetPath);
        await this.page.waitForLoadState('networkidle');

        // 截图
        const screenshot = await this.capture(
          `${checkpoint.id}_${i}`,
          'page_loaded'
        );

        // 断言
        const currentUrl = this.page.url();
        const isAllowed = testCase.expected === 'allowed';
        const hasAccess = currentUrl.includes(targetPath);

        const result: TestResult = {
          checkpoint_id: checkpoint.id,
          case_index: i,
          description: `${testCase.role} ${testCase.action} ${targetPath}`,
          expected: testCase.expected,
          actual: hasAccess ? 'allowed' : 'denied',
          result: (isAllowed === hasAccess) ? 'PASS' : 'FAIL',
          screenshot,
          duration: Date.now() - startTime,
        };

        this.results.push(result);

        // 登出
        await this.logout();

      } catch (error) {
        this.results.push({
          checkpoint_id: checkpoint.id,
          case_index: i,
          description: `${testCase.role} ${testCase.action} ${targetPath}`,
          expected: testCase.expected,
          actual: 'error',
          result: 'FAIL',
          error: String(error),
          duration: Date.now() - startTime,
        });
      }
    }
  }

  /**
   * 执行 UI 测试
   */
  async executeUITest(checkpoint: Checkpoint): Promise<void> {
    for (let i = 0; i < checkpoint.cases.length; i++) {
      const testCase = checkpoint.cases[i];
      const startTime = Date.now();

      try {
        const locator = this.page.locator(testCase.selector!);

        // 等待元素
        await locator.waitFor({ timeout: 5000 });

        // 断言
        let actual: string;
        let passed: boolean;

        if (testCase.expected_text) {
          actual = await locator.textContent() || '';
          passed = actual.includes(testCase.expected_text);
        } else if (testCase.expected === 'visible') {
          passed = await locator.isVisible();
          actual = passed ? 'visible' : 'hidden';
        } else {
          passed = false;
          actual = 'unknown';
        }

        const screenshot = await this.capture(
          `${checkpoint.id}_${i}`,
          'ui_check'
        );

        this.results.push({
          checkpoint_id: checkpoint.id,
          case_index: i,
          description: `检查元素 ${testCase.selector}`,
          expected: testCase.expected_text || testCase.expected,
          actual,
          result: passed ? 'PASS' : 'FAIL',
          screenshot,
          duration: Date.now() - startTime,
        });

      } catch (error) {
        this.results.push({
          checkpoint_id: checkpoint.id,
          case_index: i,
          description: `检查元素 ${testCase.selector}`,
          expected: testCase.expected_text || testCase.expected,
          actual: 'error',
          result: 'FAIL',
          error: String(error),
          duration: Date.now() - startTime,
        });
      }
    }
  }

  /**
   * 生成追溯报告
   */
  generateReport(moduleName: string): string {
    const passed = this.results.filter(r => r.result === 'PASS').length;
    const failed = this.results.filter(r => r.result === 'FAIL').length;
    const total = this.results.length;

    let report = `## 测试追溯报告: ${moduleName}\n\n`;
    report += `### 1. 执行摘要\n`;
    report += `- 执行时间: ${new Date().toISOString()}\n`;
    report += `- 总用例数: ${total}\n`;
    report += `- 通过: ${passed}\n`;
    report += `- 失败: ${failed}\n`;
    report += `- 通过率: ${((passed / total) * 100).toFixed(1)}%\n\n`;

    report += `### 2. 详细结果\n\n`;
    report += `| 检查点 | 用例 | 预期 | 实际 | 结果 | 耗时 |\n`;
    report += `|--------|------|------|------|------|------|\n`;

    for (const r of this.results) {
      const icon = r.result === 'PASS' ? '✅' : '❌';
      report += `| ${r.checkpoint_id} | ${r.description} | ${r.expected} | ${r.actual} | ${icon} | ${r.duration}ms |\n`;
    }

    report += `\n### 3. 截图清单\n`;
    for (const s of this.screenshots) {
      report += `- ${s}\n`;
    }

    if (failed > 0) {
      report += `\n### 4. 失败详情\n`;
      for (const r of this.results.filter(r => r.result === 'FAIL')) {
        report += `\n#### ${r.checkpoint_id} - ${r.description}\n`;
        report += `- 预期: ${r.expected}\n`;
        report += `- 实际: ${r.actual}\n`;
        if (r.error) report += `- 错误: ${r.error}\n`;
        if (r.screenshot) report += `- 截图: ${r.screenshot}\n`;
      }
    }

    return report;
  }
}
```

### 6.2 测试入口

```typescript
// tests/e2e/modules/B2-daily-report-review.spec.ts

import { test, expect } from '@playwright/test';
import { AITestExecutor } from '../../ai-test-executor';

test.describe('B2-日报审核模块测试', () => {
  let executor: AITestExecutor;

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    executor = new AITestExecutor(page);
  });

  test('执行完整测试套件', async ({ page }) => {
    executor = new AITestExecutor(page);

    // 1. 加载检查点
    const checkpoints = executor.loadCheckpoints('B2-daily-report-review');
    console.log(`加载 ${checkpoints.length} 个检查点`);

    // 2. 执行权限测试
    const permissionCP = checkpoints.find(cp => cp.id === 'CP-B2-001');
    if (permissionCP) {
      await executor.executePermissionTest(permissionCP, '/daily-reports/review');
    }

    // 3. 执行 UI 测试（需要先登录）
    await executor.login('supervisor');
    await page.goto('/daily-reports/review');
    await page.waitForLoadState('networkidle');

    const uiCP = checkpoints.find(cp => cp.id === 'CP-B2-002');
    if (uiCP) {
      await executor.executeUITest(uiCP);
    }

    // 4. 生成报告
    const report = executor.generateReport('B2-daily-report-review');
    console.log(report);

    // 5. 保存报告
    const fs = require('fs');
    fs.writeFileSync('test-results/B2-daily-report-review-report.md', report);
  });
});
```

---

## 第七章 完整性保证机制

### 7.1 覆盖率检查脚本

```typescript
// scripts/check-test-coverage.ts

import * as yaml from 'js-yaml';
import * as fs from 'fs';
import * as glob from 'glob';

interface CoverageReport {
  module: string;
  spec_sections: { total: number; covered: number };
  checkpoints: { total: number; covered: number };
  test_cases: { total: number; executed: number; passed: number };
  roles: { total: 7; tested: number };
  uncovered: string[];
}

/**
 * 检查测试覆盖完整性
 */
function checkCoverage(): CoverageReport[] {
  const reports: CoverageReport[] = [];

  // 扫描所有检查点文件
  const checkpointFiles = glob.sync('checkpoints/*.yaml');

  for (const file of checkpointFiles) {
    const content = fs.readFileSync(file, 'utf-8');
    const data = yaml.load(content) as any;

    // 检查是否有对应的测试结果
    const moduleName = data.module;
    const resultFile = `test-results/${moduleName}-report.md`;

    if (!fs.existsSync(resultFile)) {
      reports.push({
        module: moduleName,
        spec_sections: { total: 0, covered: 0 },
        checkpoints: { total: data.checkpoints.length, covered: 0 },
        test_cases: { total: 0, executed: 0, passed: 0 },
        roles: { total: 7, tested: 0 },
        uncovered: [`整个模块未测试: ${moduleName}`],
      });
      continue;
    }

    // 解析测试结果
    // ... 解析逻辑
  }

  return reports;
}

/**
 * 生成覆盖率报告
 */
function generateCoverageReport(reports: CoverageReport[]): string {
  let output = '# 测试覆盖率报告\n\n';

  output += '## 总览\n\n';
  output += '| 模块 | 检查点 | 用例 | 通过率 | 角色覆盖 |\n';
  output += '|------|--------|------|--------|----------|\n';

  for (const r of reports) {
    const cpCoverage = `${r.checkpoints.covered}/${r.checkpoints.total}`;
    const tcCoverage = `${r.test_cases.passed}/${r.test_cases.executed}`;
    const roleCoverage = `${r.roles.tested}/7`;
    output += `| ${r.module} | ${cpCoverage} | ${tcCoverage} | ${roleCoverage} |\n`;
  }

  // 未覆盖项
  const allUncovered = reports.flatMap(r => r.uncovered);
  if (allUncovered.length > 0) {
    output += '\n## ⚠️ 未覆盖项\n\n';
    for (const item of allUncovered) {
      output += `- ${item}\n`;
    }
  }

  return output;
}

// 执行检查
const reports = checkCoverage();
const report = generateCoverageReport(reports);
console.log(report);
fs.writeFileSync('test-results/coverage-report.md', report);
```

### 7.2 CI 集成检查

```yaml
# .github/workflows/test-coverage-check.yml

name: Test Coverage Check

on:
  pull_request:
    branches: [main, develop]

jobs:
  coverage-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check checkpoint files exist
        run: |
          for spec in docs/5.module-specs/*.md; do
            module=$(basename "$spec" .md)
            if [ ! -f "checkpoints/${module}.yaml" ]; then
              echo "❌ Missing checkpoint file for: $module"
              exit 1
            fi
          done
          echo "✅ All checkpoint files exist"

      - name: Run tests
        run: pnpm test:e2e

      - name: Check coverage
        run: |
          node scripts/check-test-coverage.ts
          
          # 检查是否有未覆盖项
          if grep -q "未覆盖项" test-results/coverage-report.md; then
            echo "❌ Found uncovered items"
            cat test-results/coverage-report.md
            exit 1
          fi
          echo "✅ All items covered"

      - name: Upload coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: test-results/
```

---

## 第八章 AI 测试执行 SOP

### 8.1 标准操作流程

```markdown
## AI 测试执行 SOP

### Phase 1: 准备阶段

1. **读取规格书**
   ```
   读取: docs/5.module-specs/{module}.md
   提取: 业务目标、用户角色、数据需求、UI 规范、API 接口
   ```

2. **加载检查点清单**
   ```
   读取: checkpoints/{module}.yaml
   确认: 检查点数量、测试用例数量
   ```

3. **验证测试环境**
   ```
   检查: 前端服务 http://localhost:3000
   检查: Mock API 服务
   检查: 7 个测试账号可用
   ```

4. **输出执行计划**
   ```
   模块: {module}
   检查点: X 个
   测试用例: Y 个
   预计耗时: Z 分钟
   ```

### Phase 2: 执行阶段

5. **按检查点顺序执行**
   - CP-001 权限测试（7 角色）
   - CP-002 UI 测试
   - CP-003 数据测试
   - CP-004 功能测试
   - CP-005 Phase 1 规则测试

6. **每个测试用例输出**
   ```
   执行: TC-{id}
   步骤: 1. xxx 2. xxx 3. xxx
   断言: | 类型 | 预期 | 实际 | 结果 |
   截图: screenshots/{id}.png
   ```

### Phase 3: 报告阶段

7. **生成追溯报告**
   - 执行摘要
   - 覆盖率统计
   - 详细结果表格
   - 追溯矩阵
   - 截图清单

8. **检查完整性**
   - 所有检查点已覆盖 ✓
   - 所有角色已测试 ✓
   - 无未覆盖项 ✓

9. **输出最终结论**
   ```
   ✅ 测试通过，覆盖率 100%
   或
   ❌ 测试失败，X 个用例失败，需要修复
   ```
```

### 8.2 AI 执行指令模板

当用户要求执行测试时，AI 使用以下模板：

```markdown
## 测试执行: {module}

### 1. 准备检查
□ 规格书已读取: docs/5.module-specs/{module}.md
□ 检查点已加载: checkpoints/{module}.yaml
□ 检查点数量: X 个
□ 测试用例数量: Y 个

### 2. 执行计划
| 检查点 | 类别 | 用例数 | 预计耗时 |
|--------|------|--------|----------|
| CP-001 | 权限 | 7 | 2min |
| CP-002 | UI | 3 | 1min |
| ... | ... | ... | ... |

### 3. 开始执行

[执行 CP-001]
...

### 4. 追溯报告
[完整追溯报告]

### 5. 结论
✅/❌ 测试结果
```

---

## 附录 A: 检查点清单模板

```yaml
# checkpoints/TEMPLATE.yaml

module: "{MODULE_NAME}"
spec_file: "docs/5.module-specs/{MODULE}.md"
version: "1.0"

checkpoints:
  # 权限检查点（必须）
  - id: CP-{MODULE}-001
    category: permission
    description: 页面访问权限
    spec_ref: "§1.2 用户角色"
    cases:
      - role: ceo
        action: access
        expected: allowed/denied
      # ... 7 个角色全部列出

  # UI 检查点（必须）
  - id: CP-{MODULE}-002
    category: ui
    description: 页面元素渲染
    spec_ref: "§3 UI 规范"
    cases:
      - element: page_title
        selector: "h1"
        expected_text: "{标题}"
      # ... 关键元素

  # 数据检查点（必须）
  - id: CP-{MODULE}-003
    category: data
    description: 数据加载与显示
    spec_ref: "§2 数据需求"
    cases:
      - scenario: loading_state
        expected: "显示加载状态"
      - scenario: empty_state
        expected: "显示空状态"
      - scenario: data_loaded
        expected: "显示数据"

  # 功能检查点（按需）
  - id: CP-{MODULE}-004
    category: function
    description: 核心功能
    spec_ref: "§5 API 接口"
    cases:
      - action: "{操作}"
        expected: "{结果}"

  # Phase 1 检查点（必须）
  - id: CP-{MODULE}-005
    category: phase1
    description: Phase 1 规则验证
    spec_ref: "MASTER.md §3.1"
    cases:
      - scenario: abnormal_data
        expected: "高亮显示，不阻断操作"

summary:
  total_checkpoints: 5
  total_cases: X
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本 |

---

**文档维护者**: AI 编程助手
**核心保证**: 规格书驱动 + 检查点清单 + 双重验证 + 追溯矩阵
