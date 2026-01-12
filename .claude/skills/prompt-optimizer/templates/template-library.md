# 提示词模板库

> 版本: v1.0 | 更新: 2026-01-06

---

## 模板索引

| ID | 模板名称 | 任务类型 | 关键词 | 文件 |
|----|----------|----------|--------|------|
| TPL-001 | API 测试用例 | 测试 | api, 测试, test, 用例, endpoint | `api-test.md` |
| TPL-002 | 代码审查 | 审查 | 审查, review, 安全, 代码检查 | `code-review.md` |
| TPL-003 | 信息提取 | 提取 | 提取, extract, 解析, parse | `info-extract.md` |
| TPL-004 | 内容生成 | 生成 | 写, 生成, 创建, 博客, 文档 | `content-gen.md` |
| TPL-005 | 分类判断 | 分类 | 分类, classify, 情感, sentiment | `classify.md` |
| TPL-006 | 数据转换 | 转换 | 转换, convert, 格式, format | `data-transform.md` |
| TPL-007 | 问题分析 | 分析 | 分析, analyze, 问题, debug, 排查 | `problem-analysis.md` |
| TPL-008 | SQL 生成 | 生成 | sql, 查询, 数据库, query | `sql-gen.md` |

---

## 模板匹配规则

### 匹配优先级

1. **精确关键词匹配**: 用户输入包含模板的精确关键词
2. **任务类型匹配**: 根据动词推断任务类型
3. **默认模板**: 无法匹配时使用通用模板 (`standard.md`)

### 任务类型-动词映射

| 任务类型 | 触发动词 |
|----------|----------|
| 测试 | 测试、test、验证、检验、写测试 |
| 审查 | 审查、review、检查、审核、扫描 |
| 提取 | 提取、extract、解析、parse、获取 |
| 生成 | 写、生成、创建、撰写、编写 |
| 分类 | 分类、classify、判断、识别、标注 |
| 转换 | 转换、convert、格式化、format、变换 |
| 分析 | 分析、analyze、诊断、排查、debug |

---

## 模板加载流程

```
用户输入 → [1]关键词匹配 → [2]任务类型推断 → [3]加载模板 → [4]填充变量 → 输出
```

### Step 1: 关键词匹配

```yaml
input: "编写 API 测试用例"
match:
  - keyword: "API" → TPL-001
  - keyword: "测试" → TPL-001
result: TPL-001 (confidence: high)
```

### Step 2: 任务类型推断

```yaml
input: "分析这段代码的性能问题"
verbs: ["分析"]
task_type: "分析"
result: TPL-007 (confidence: medium)
```

### Step 3: 加载模板

```
读取: templates/{template_file}
变量: 从用户输入中提取
```

---

## 模板变量规范

所有模板支持以下变量替换：

| 变量 | 说明 | 示例 |
|------|------|------|
| `{topic}` | 主题/对象 | "用户认证模块" |
| `{language}` | 编程语言 | "Python", "TypeScript" |
| `{framework}` | 框架 | "FastAPI", "Next.js" |
| `{audience}` | 目标受众 | "初级开发者" |
| `{format}` | 输出格式 | "JSON", "Markdown" |

---

## 使用示例

### 示例 1: API 测试

```bash
/pc 为 POST /api/v1/users 编写测试用例
```

匹配过程：
- 关键词: "API", "测试" → TPL-001
- 加载: `templates/api-test.md`
- 变量: `{endpoint}` = "POST /api/v1/users"

### 示例 2: 代码审查

```bash
/pc Python 代码安全审查
```

匹配过程：
- 关键词: "审查", "安全" → TPL-002
- 加载: `templates/code-review.md`
- 变量: `{language}` = "Python", `{focus}` = "安全"

### 示例 3: 未匹配

```bash
/pc 帮我优化这个算法
```

匹配过程：
- 关键词: 无精确匹配
- 动词: "优化" → 无直接映射
- 回退: `templates/standard.md`

---

## 扩展模板

### 添加新模板步骤

1. 在 `templates/` 目录创建新模板文件
2. 更新本文件的"模板索引"表格
3. 添加相关关键词和任务类型映射
4. 验证模板符合 7 必需标签规范

### 模板文件格式要求

每个模板文件必须包含：

```markdown
# 模板名称

> 类型: {任务类型} | 关键词: {keyword1}, {keyword2}

---

## 模板内容

```xml
<role>
...
</role>
...
```
